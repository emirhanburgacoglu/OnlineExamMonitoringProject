from fastapi import FastAPI

app = FastAPI(title="Online Exam Monitoring API")


@app.get("/")

def read_root():

    return {"message": "Merhaba! Analiz API'si çalışıyor"}