-- Create sample aircraft for testing
DO $
DECLARE
    default_org_id UUID;
BEGIN
    -- Get default organization ID
    SELECT org_id INTO default_org_id 
    FROM dbx_aviation.organizations 
    WHERE org_code = 'DBX_DEFAULT';
    
    IF default_org_id IS NOT NULL THEN
        -- Create sample aircraft
        INSERT INTO dbx_aviation.aircraft_registry (
            org_id, registration_number, aircraft_type, manufacturer, model,
            specifications, operational_status
        ) VALUES 
        (
            default_org_id, 'TEST-001', 'multirotor', 'DJI', 'Phantom 4 Pro',
            '{
                "motors": {"count": 4, "type": "brushless", "max_rpm": 15000},
                "dimensions": {"length_m": 0.35, "wingspan_m": 0.35, "height_m": 0.20},
                "weight": {"empty_kg": 1.4, "max_takeoff_kg": 1.8},
                "performance": {
                    "max_speed_ms": 20,
                    "cruise_speed_ms": 15,
                    "max_altitude_m": 6000,
                    "endurance_minutes": 30
                },
                "sensors": ["gps", "imu", "barometer", "magnetometer", "camera"]
            }'::jsonb,
            'active'
        ),
        (
            default_org_id, 'TEST-002', 'fixed_wing', 'Cessna', 'C172',
            '{
                "motors": {"count": 1, "type": "piston", "max_rpm": 2700},
                "dimensions": {"length_m": 8.28, "wingspan_m": 11.0, "height_m": 2.72},
                "weight": {"empty_kg": 767, "max_takeoff_kg": 1157},
                "performance": {
                    "max_speed_ms": 67,
                    "cruise_speed_ms": 56,
                    "stall_speed_ms": 24,
                    "max_altitude_m": 4267,
                    "endurance_minutes": 240
                },
                "sensors": ["gps", "attitude_indicator", "altimeter", "airspeed"],
                "control_surfaces": ["elevator", "aileron", "rudder", "flaps"]
            }'::jsonb,
            'active'
        ),
        (
            default_org_id, 'TEST-003', 'vtol', 'Bell', 'V-280 Valor',
            '{
                "motors": {"count": 2, "type": "turboshaft", "max_rpm": 6000},
                "dimensions": {"length_m": 15.5, "wingspan_m": 18.3, "height_m": 4.6},
                "weight": {"empty_kg": 6800, "max_takeoff_kg": 12700},
                "performance": {
                    "max_speed_ms": 139,
                    "cruise_speed_ms": 111,
                    "hover_ceiling_m": 1829,
                    "max_altitude_m": 7620,
                    "endurance_minutes": 180
                },
                "sensors": ["gps", "radar", "lidar", "eo_ir_camera", "weather_radar"],
                "control_surfaces": ["elevator", "aileron", "rudder"],
                "vtol_capability": true
            }'::jsonb,
            'active'
        )
        ON CONFLICT (org_id, registration_number) DO NOTHING;
        
        RAISE NOTICE 'Sample aircraft created: TEST-001 (Multirotor), TEST-002 (Fixed Wing), TEST-003 (VTOL)';
    END IF;
END $;