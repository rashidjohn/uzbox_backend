import multiprocessing

# Worker sozlamalari
workers     = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout     = 30
keepalive   = 2

# Binding
bind        = "0.0.0.0:8000"

# Logging
accesslog   = "-"
errorlog    = "-"
loglevel    = "warning"

# Process nomi
proc_name   = "uzbox_backend"

# Xavfsizlik
limit_request_line   = 4094
limit_request_fields = 100
