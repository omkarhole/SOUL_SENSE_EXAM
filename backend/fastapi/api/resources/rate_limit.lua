local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local request_id = ARGV[4]
local clear_before = now - window

-- 1. Remove old requests from the window
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

-- 2. Count current requests
local count = redis.call('ZCARD', key)
local allowed = count < limit

if allowed then
    -- 3. Add the new request timestamp with unique ID
    redis.call('ZADD', key, now, request_id)
end

-- 4. Set expiry to clean up idle keys
redis.call('EXPIRE', key, window + 1)

return {allowed and 1 or 0, limit - count - (allowed and 1 or 0)}
