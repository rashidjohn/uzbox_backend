# Railway bepul plan uchun optimallashtirilgan

workers     = 2          # kam xotira uchun (CPU*2+1 emas)
worker_class = "sync"
timeout     = 120
keepalive   = 2
bind        = "0.0.0.0:8000"
accesslog   = "-"
errorlog    = "-"
loglevel    = "warning"
proc_name   = "uzbox_backend"

# Xotira tejash
max_requests        = 1000
max_requests_jitter = 100
preload_app         = False   # preload o'chirildi — xotira tejaydi