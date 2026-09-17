CREATE TABLE IF NOT EXISTS checks(test_id TEXT PRIMARY KEY,device TEXT NOT NULL,received_at INTEGER NOT NULL,observed_ip TEXT,expected_ip TEXT,result TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS checks_time ON checks(received_at);
CREATE INDEX IF NOT EXISTS checks_device_time ON checks(device,received_at);
