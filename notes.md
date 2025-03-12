# Creating the self-published tls certificate
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes

# Troubleshoot bankend connnection
Will produce output if the server is running
```
lsof -i :8080 
```

Will return html if FastAPI is running
```
curl -k https://localhost:8080/docs
```

# Build and run docker
```
docker build -t flare-ai-defai . && docker run -p 80:80 -p 8080:8080 -it --env-file .env flare-ai-defai
```

# uv
```
uv add package1 package2
```

# Colour scheme
Midnight Blue (#1A2A44) – Trustworthy base
Electric Cyan (#00D4FF) – Modern crypto accent
Soft Gray (#E8ECEF) – Clean neutral
Success Green (#34C759) – Positive feedback
Warm Orange (#FF9500) – Alerts