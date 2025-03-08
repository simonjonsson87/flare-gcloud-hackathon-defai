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