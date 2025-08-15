"""
DBX AI Aviation Database - Python Integration Module
Production-ready database integration with all enhanced features
"""

import os
import json
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from contextlib import asynccontextmanager
import logging

import asyncpg
import redis.asyncio as redis
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, select, insert, update, delete
import bcrypt
import jwt
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

class DatabaseConfig(BaseModel):
    """Database configuration settings"""
    database_url: str = Field(default="postgresql+asyncpg://dbx_app_user:change_me@localhost:5432/dbx_aviation")
    redis_url: str = Field(default="redis://localhost:6379")
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=40)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    echo_sql: bool = Field(default=False)

class SecurityConfig(BaseModel):
    """Security configuration settings"""
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    password_min_length: int = Field(default=8)
    max_login_attempts: int = Field(default=5)
    lockout_duration_minutes: int = Field(default=15)
    encryption_key: Optional[str] = None

class CacheConfig(BaseModel):
    """Cache configuration settings"""
    default_ttl: int = Field(default=3600)  # 1 hour
    max_connections: int = Field(default=10)
    retry_on_timeout: bool = Field(default=True)
    health_check_interval: int = Field(default=30)

# ============================================
# DATABASE CONNECTION MANAGER
# ============================================

class DatabaseManager:
    """Advanced database connection manager with connection pooling"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
        self._connection_pool = None
        
    async def initialize(self):
        """Initialize database connections and pools"""
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo_sql,
                pool_pre_ping=True  # Validate connections before use
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper error handling"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def set_org_context(self, session: AsyncSession, org_id: str):
        """Set organization context for Row Level Security"""
        await session.execute(
            text("SELECT dbx_aviation.set_org_context(:org_id)"),
            {"org_id": org_id}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and return metrics"""
        try:
            async with self.get_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT NOW()"))
                timestamp = result.scalar()
                
                # Get connection pool stats
                pool = self.engine.pool
                pool_stats = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
                
                # Get database performance metrics
                perf_result = await session.execute(
                    text("SELECT * FROM dbx_aviation.database_performance")
                )
                performance_metrics = {row.metric: row.value for row in perf_result}
                
                return {
                    "status": "healthy",
                    "timestamp": timestamp,
                    "pool_stats": pool_stats,
                    "performance_metrics": performance_metrics
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# ============================================
# CACHE MANAGER
# ============================================

class CacheManager:
    """Redis-based cache manager with smart invalidation"""
    
    def __init__(self, config: CacheConfig, redis_url: str):
        self.config = config
        self.redis_url = redis_url
        self.redis_client = None
        self._cache_policies = {}
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
            # Load cache policies
            await self._load_cache_policies()
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def _load_cache_policies(self):
        """Load cache policies from database"""
        # This would typically load from the database
        # For now, using default policies
        self._cache_policies = {
            "flight_analysis": {"ttl": 7200, "pattern": "analysis:{org_id}:{session_id}"},
            "aircraft_registry": {"ttl": 21600, "pattern": "aircraft:{org_id}:{aircraft_id}"},
            "user_sessions": {"ttl": 1800, "pattern": "user_session:{session_token}"},
            "rate_limits": {"ttl": 60, "pattern": "rate_limit:{org_id}:{api_key}:{window}"},
            "system_health": {"ttl": 300, "pattern": "health:{component}:{timestamp}"}
        }
    
    def _generate_cache_key(self, policy_name: str, **kwargs) -> str:
        """Generate cache key based on policy and parameters"""
        if policy_name not in self._cache_policies:
            raise ValueError(f"Unknown cache policy: {policy_name}")
        
        pattern = self._cache_policies[policy_name]["pattern"]
        
        # Replace placeholders with actual values
        for key, value in kwargs.items():
            pattern = pattern.replace(f"{{{key}}}", str(value))
        
        return pattern
    
    async def get(self, policy_name: str, **kwargs) -> Optional[Any]:
        """Get cached value"""
        try:
            cache_key = self._generate_cache_key(policy_name, **kwargs)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Record cache hit
                await self._record_cache_stat(policy_name, "hit")
                return json.loads(cached_data)
            else:
                # Record cache miss
                await self._record_cache_stat(policy_name, "miss")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, policy_name: str, value: Any, ttl: Optional[int] = None, **kwargs):
        """Set cached value"""
        try:
            cache_key = self._generate_cache_key(policy_name, **kwargs)
            ttl = ttl or self._cache_policies[policy_name]["ttl"]
            
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            # Record cache set
            await self._record_cache_stat(policy_name, "set")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, policy_name: str, **kwargs):
        """Delete cached value"""
        try:
            cache_key = self._generate_cache_key(policy_name, **kwargs)
            await self.redis_client.delete(cache_key)
            
            # Record cache delete
            await self._record_cache_stat(policy_name, "delete")
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache keys matching pattern"""
        try:
            # Use Lua script for atomic pattern deletion
            lua_script = """
                local pattern = KEYS[1]
                local keys = redis.call("KEYS", pattern)
                local deleted = 0
                for i=1,#keys do
                    redis.call("DEL", keys[i])
                    deleted = deleted + 1
                end
                return deleted
            """
            
            deleted_count = await self.redis_client.eval(lua_script, 1, pattern)
            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0
    
    async def _record_cache_stat(self, policy_name: str, operation: str):
        """Record cache statistics (simplified version)"""
        # In production, this would call the database function
        # For now, just log the operation
        logger.debug(f"Cache {operation} for policy: {policy_name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            info = await self.redis_client.info()
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

# ============================================
# AUTHENTICATION MANAGER
# ============================================

class AuthenticationManager:
    """Comprehensive authentication and session management"""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager, 
                 security_config: SecurityConfig):
        self.db = db_manager
        self.cache = cache_manager
        self.config = security_config
        
        # Initialize encryption if key provided
        if security_config.encryption_key:
            self.cipher = Fernet(security_config.encryption_key.encode())
        else:
            self.cipher = None
    
    def _hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt using bcrypt"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8'), salt.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": str(user_data["user_id"]),
            "org_id": str(user_data["org_id"]),
            "role": user_data["role"],
            "exp": datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str, 
                              ip_address: Optional[str] = None,
                              user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate user and create session"""
        async with self.db.get_session() as session:
            # Call database authentication function
            result = await session.execute(
                text("SELECT dbx_aviation.authenticate_user(:email, :password, :ip_address, :user_agent)"),
                {
                    "email": email,
                    "password": password,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
            
            auth_result = result.scalar()
            
            if auth_result["success"]:
                # Generate JWT token
                jwt_token = self._generate_jwt_token(auth_result)
                
                # Cache session data
                await self.cache.set(
                    "user_sessions",
                    {
                        "user_id": auth_result["user_id"],
                        "org_id": auth_result["org_id"],
                        "role": auth_result["role"],
                        "permissions": auth_result["permissions"]
                    },
                    session_token=jwt_token
                )
                
                return {
                    "success": True,
                    "token": jwt_token,
                    "user_id": auth_result["user_id"],
                    "org_id": auth_result["org_id"],
                    "role": auth_result["role"]
                }
            else:
                return {"success": False, "error": auth_result["error"]}
    
    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token"""
        # First check cache
        cached_session = await self.cache.get("user_sessions", session_token=token)
        if cached_session:
            return cached_session
        
        # Verify JWT token
        payload = self._verify_jwt_token(token)
        if not payload:
            return None
        
        # Validate with database
        async with self.db.get_session() as session:
            result = await session.execute(
                text("SELECT dbx_aviation.validate_session(:token)"),
                {"token": token}
            )
            
            validation_result = result.scalar()
            
            if validation_result["valid"]:
                # Cache the session data
                await self.cache.set(
                    "user_sessions",
                    validation_result,
                    session_token=token
                )
                
                return validation_result
            else:
                return None
    
    async def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate API key"""
        async with self.db.get_session() as session:
            result = await session.execute(
                text("SELECT dbx_aviation.get_org_by_api_key(:api_key)"),
                {"api_key": api_key}
            )
            
            auth_result = result.scalar()
            
            if auth_result["valid"]:
                return auth_result
            else:
                return None
    
    async def create_user(self, org_id: str, email: str, password: str,
                         first_name: str, last_name: str, role: str = "user") -> Dict[str, Any]:
        """Create new user account"""
        # Validate password strength
        if len(password) < self.config.password_min_length:
            return {"success": False, "error": f"Password must be at least {self.config.password_min_length} characters"}
        
        # Hash password
        password_hash, salt = self._hash_password(password)
        
        async with self.db.get_session() as session:
            try:
                # Insert user
                result = await session.execute(
                    text("""
                        INSERT INTO dbx_aviation.users 
                        (org_id, email, password_hash, salt, first_name, last_name, role, email_verified)
                        VALUES (:org_id, :email, :password_hash, :salt, :first_name, :last_name, :role, false)
                        RETURNING user_id
                    """),
                    {
                        "org_id": org_id,
                        "email": email,
                        "password_hash": password_hash,
                        "salt": salt,
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": role
                    }
                )
                
                user_id = result.scalar()
                
                return {
                    "success": True,
                    "user_id": str(user_id),
                    "message": "User created successfully"
                }
                
            except Exception as e:
                logger.error(f"User creation failed: {e}")
                return {"success": False, "error": "User creation failed"}

# ============================================
# MAIN DATABASE CLIENT
# ============================================

class DBXDatabaseClient:
    """Main database client with all enhanced features"""
    
    def __init__(self, database_config: DatabaseConfig, cache_config: CacheConfig,
                 security_config: SecurityConfig):
        self.db_config = database_config
        self.cache_config = cache_config
        self.security_config = security_config
        
        # Initialize managers
        self.db = DatabaseManager(database_config)
        self.cache = CacheManager(cache_config, database_config.redis_url)
        self.auth = AuthenticationManager(self.db, self.cache, security_config)
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize all database components"""
        if self._initialized:
            return
        
        try:
            await self.db.initialize()
            await self.cache.initialize()
            self._initialized = True
            logger.info("DBX Database Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database client: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        db_health = await self.db.health_check()
        cache_health = await self.cache.health_check()
        
        overall_status = "healthy" if (
            db_health["status"] == "healthy" and 
            cache_health["status"] == "healthy"
        ) else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "database": db_health,
            "cache": cache_health,
            "timestamp": datetime.utcnow()
        }
    
    async def get_flight_analysis(self, org_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get flight analysis with caching"""
        # Try cache first
        cached_result = await self.cache.get("flight_analysis", org_id=org_id, session_id=session_id)
        if cached_result:
            return cached_result
        
        # Query database
        async with self.db.get_session() as session:
            await self.db.set_org_context(session, org_id)
            
            result = await session.execute(
                text("""
                    SELECT mar.*, fs.flight_number, ar.registration_number
                    FROM dbx_aviation.ml_analysis_results mar
                    JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
                    JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
                    WHERE mar.session_id = :session_id
                    ORDER BY mar.analysis_timestamp DESC
                    LIMIT 1
                """),
                {"session_id": session_id}
            )
            
            row = result.fetchone()
            if row:
                analysis_data = dict(row._mapping)
                
                # Cache the result
                await self.cache.set("flight_analysis", analysis_data, org_id=org_id, session_id=session_id)
                
                return analysis_data
            
            return None
    
    async def save_flight_analysis(self, org_id: str, session_id: str, 
                                 analysis_data: Dict[str, Any]) -> str:
        """Save flight analysis and invalidate cache"""
        async with self.db.get_session() as session:
            await self.db.set_org_context(session, org_id)
            
            # Save analysis
            result = await session.execute(
                text("""
                    INSERT INTO dbx_aviation.ml_analysis_results 
                    (session_id, org_id, model_version, model_type, detected_aircraft_type,
                     aircraft_confidence, anomaly_detected, anomaly_score, risk_score, risk_level,
                     anomalies, shap_values, ai_report_content)
                    VALUES (:session_id, :org_id, :model_version, :model_type, :detected_aircraft_type,
                            :aircraft_confidence, :anomaly_detected, :anomaly_score, :risk_score, :risk_level,
                            :anomalies, :shap_values, :ai_report_content)
                    RETURNING analysis_id
                """),
                {
                    "session_id": session_id,
                    "org_id": org_id,
                    "model_version": analysis_data.get("model_version", "2.0.0"),
                    "model_type": "multi_aircraft_detection",
                    "detected_aircraft_type": analysis_data.get("detected_aircraft_type"),
                    "aircraft_confidence": analysis_data.get("aircraft_confidence"),
                    "anomaly_detected": analysis_data.get("anomaly_detected", False),
                    "anomaly_score": analysis_data.get("anomaly_score"),
                    "risk_score": analysis_data.get("risk_score"),
                    "risk_level": analysis_data.get("risk_level"),
                    "anomalies": json.dumps(analysis_data.get("anomalies", [])),
                    "shap_values": json.dumps(analysis_data.get("shap_values", {})),
                    "ai_report_content": analysis_data.get("ai_report_content")
                }
            )
            
            analysis_id = result.scalar()
            
            # Invalidate cache
            await self.cache.delete("flight_analysis", org_id=org_id, session_id=session_id)
            
            return str(analysis_id)
    
    async def get_recent_analyses(self, org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results"""
        async with self.db.get_session() as session:
            await self.db.set_org_context(session, org_id)
            
            result = await session.execute(
                text("SELECT * FROM dbx_aviation.get_recent_analyses(:org_id, :limit)"),
                {"org_id": org_id, "limit": limit}
            )
            
            return [dict(row._mapping) for row in result.fetchall()]
    
    async def close(self):
        """Close all connections"""
        await self.db.close()
        await self.cache.close()
        logger.info("DBX Database Client closed")

# ============================================
# USAGE EXAMPLE
# ============================================

async def main():
    """Example usage of the DBX Database Client"""
    
    # Configuration
    db_config = DatabaseConfig(
        database_url="postgresql+asyncpg://dbx_app_user:change_me@localhost:5432/dbx_aviation"
    )
    cache_config = CacheConfig()
    security_config = SecurityConfig()
    
    # Initialize client
    client = DBXDatabaseClient(db_config, cache_config, security_config)
    await client.initialize()
    
    try:
        # Health check
        health = await client.health_check()
        print(f"System Health: {health['overall_status']}")
        
        # Authenticate user
        auth_result = await client.auth.authenticate_user(
            email="admin@dbx-ai.com",
            password="admin123",
            ip_address="127.0.0.1"
        )
        
        if auth_result["success"]:
            print(f"Authentication successful: {auth_result['role']}")
            
            # Get recent analyses
            analyses = await client.get_recent_analyses(auth_result["org_id"])
            print(f"Found {len(analyses)} recent analyses")
            
        else:
            print(f"Authentication failed: {auth_result['error']}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())