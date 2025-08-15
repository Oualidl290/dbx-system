#!/bin/bash
# 🚀 DBX AI Aviation System - Enterprise Deployment Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENVIRONMENT="${1:-staging}"
IMAGE_TAG="${2:-latest}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}❌ Error: Environment must be 'staging' or 'production'${NC}"
    echo "Usage: $0 <environment> [image_tag]"
    exit 1
fi

echo -e "${BLUE}🚀 Starting deployment to ${ENVIRONMENT}...${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check required tools
    local tools=("kubectl" "helm" "aws" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            echo -e "${RED}❌ Error: $tool is not installed${NC}"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ Error: AWS credentials not configured${NC}"
        exit 1
    fi
    
    # Check kubectl context
    local context="dbx-${ENVIRONMENT}"
    if ! kubectl config get-contexts | grep -q "$context"; then
        echo -e "${YELLOW}⚠️  Warning: kubectl context '$context' not found${NC}"
        echo -e "${BLUE}🔧 Updating kubeconfig...${NC}"
        aws eks update-kubeconfig --region us-west-2 --name "dbx-ai-aviation-${ENVIRONMENT}"
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    echo -e "${YELLOW}🏗️ Deploying infrastructure...${NC}"
    
    cd "$PROJECT_ROOT/deployment/terraform"
    
    # Initialize Terraform
    terraform init -backend-config="key=aviation-system/${ENVIRONMENT}/terraform.tfstate"
    
    # Plan deployment
    terraform plan -var="environment=${ENVIRONMENT}" -out="tfplan"
    
    # Apply deployment
    echo -e "${BLUE}🚀 Applying Terraform changes...${NC}"
    terraform apply "tfplan"
    
    echo -e "${GREEN}✅ Infrastructure deployment completed${NC}"
}

# Function to deploy application
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying application...${NC}"
    
    # Set kubectl context
    kubectl config use-context "dbx-${ENVIRONMENT}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$ENVIRONMENT" --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy secrets (assuming they exist in AWS Secrets Manager)
    echo -e "${BLUE}🔐 Deploying secrets...${NC}"
    deploy_secrets
    
    # Deploy application
    echo -e "${BLUE}📦 Deploying application manifests...${NC}"
    export IMAGE_TAG="$IMAGE_TAG"
    export ENVIRONMENT="$ENVIRONMENT"
    
    envsubst < "$PROJECT_ROOT/deployment/kubernetes/${ENVIRONMENT}.yaml" | kubectl apply -f -
    
    # Wait for deployment to be ready
    echo -e "${BLUE}⏳ Waiting for deployment to be ready...${NC}"
    kubectl rollout status deployment/dbx-ai-aviation -n "$ENVIRONMENT" --timeout=600s
    
    echo -e "${GREEN}✅ Application deployment completed${NC}"
}

# Function to deploy secrets
deploy_secrets() {
    local secret_name="dbx-secrets"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        secret_name="dbx-secrets-staging"
    fi
    
    # Get secrets from AWS Secrets Manager
    local database_url=$(aws secretsmanager get-secret-value --secret-id "dbx/${ENVIRONMENT}/database-url" --query SecretString --output text)
    local redis_url=$(aws secretsmanager get-secret-value --secret-id "dbx/${ENVIRONMENT}/redis-url" --query SecretString --output text)
    local secret_key=$(aws secretsmanager get-secret-value --secret-id "dbx/${ENVIRONMENT}/secret-key" --query SecretString --output text)
    
    # Create Kubernetes secret
    kubectl create secret generic "$secret_name" \
        --from-literal=database-url="$database_url" \
        --from-literal=redis-url="$redis_url" \
        --from-literal=secret-key="$secret_key" \
        --namespace="$ENVIRONMENT" \
        --dry-run=client -o yaml | kubectl apply -f -
}

# Function to deploy monitoring
deploy_monitoring() {
    echo -e "${YELLOW}📊 Deploying monitoring stack...${NC}"
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Deploy Prometheus
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --values "$PROJECT_ROOT/deployment/monitoring/prometheus-values.yaml" \
        --set prometheus.prometheusSpec.additionalScrapeConfigs[0].job_name="dbx-ai-aviation" \
        --wait
    
    # Deploy custom alert rules
    kubectl apply -f "$PROJECT_ROOT/deployment/monitoring/alert_rules.yml" -n monitoring
    
    echo -e "${GREEN}✅ Monitoring deployment completed${NC}"
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    echo -e "${YELLOW}🧪 Running post-deployment tests...${NC}"
    
    # Get service URL
    local service_url
    if [[ "$ENVIRONMENT" == "production" ]]; then
        service_url="https://api.dbx-ai.com"
    else
        service_url="https://staging.dbx-ai.com"
    fi
    
    # Health check
    echo -e "${BLUE}🔍 Checking application health...${NC}"
    local health_status=$(curl -s -o /dev/null -w "%{http_code}" "$service_url/health" || echo "000")
    
    if [[ "$health_status" == "200" ]]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed (HTTP $health_status)${NC}"
        exit 1
    fi
    
    # API functionality test
    echo -e "${BLUE}🔍 Testing API functionality...${NC}"
    local api_status=$(curl -s -o /dev/null -w "%{http_code}" "$service_url/api/v2/status" || echo "000")
    
    if [[ "$api_status" == "200" ]]; then
        echo -e "${GREEN}✅ API functionality test passed${NC}"
    else
        echo -e "${RED}❌ API functionality test failed (HTTP $api_status)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All post-deployment tests passed${NC}"
}

# Function to send deployment notification
send_notification() {
    local status="$1"
    local webhook_url="${SLACK_WEBHOOK_URL:-}"
    
    if [[ -n "$webhook_url" ]]; then
        local color="good"
        local emoji="✅"
        if [[ "$status" != "success" ]]; then
            color="danger"
            emoji="❌"
        fi
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$emoji DBX AI Aviation System Deployment",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$ENVIRONMENT",
                    "short": true
                },
                {
                    "title": "Status",
                    "value": "$status",
                    "short": true
                },
                {
                    "title": "Image Tag",
                    "value": "$IMAGE_TAG",
                    "short": true
                },
                {
                    "title": "Deployed By",
                    "value": "$(whoami)",
                    "short": true
                }
            ],
            "footer": "DBX AI Aviation System",
            "ts": $(date +%s)
        }
    ]
}
EOF
        )
        
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$webhook_url"
    fi
}

# Main deployment flow
main() {
    echo -e "${BLUE}🚀 DBX AI Aviation System - Enterprise Deployment${NC}"
    echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${BLUE}Image Tag: ${IMAGE_TAG}${NC}"
    echo ""
    
    # Deployment steps
    check_prerequisites
    
    if [[ "${SKIP_INFRASTRUCTURE:-false}" != "true" ]]; then
        deploy_infrastructure
    fi
    
    deploy_application
    
    if [[ "${SKIP_MONITORING:-false}" != "true" ]]; then
        deploy_monitoring
    fi
    
    run_post_deployment_tests
    
    echo ""
    echo -e "${GREEN}🎉 Deployment to ${ENVIRONMENT} completed successfully!${NC}"
    echo -e "${BLUE}📊 Monitoring: https://grafana.dbx-ai.com${NC}"
    echo -e "${BLUE}📚 API Docs: https://${ENVIRONMENT}.dbx-ai.com/docs${NC}"
    
    send_notification "success"
}

# Error handling
trap 'echo -e "${RED}❌ Deployment failed${NC}"; send_notification "failed"; exit 1' ERR

# Run main function
main "$@"