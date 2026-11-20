from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"student":"ok"}

@app.get("/courses/{course_id}")
def get_course(course_id: int, grade: str = "三年级"):
    return {
        "course_id":course_id,
        "grade": grade
    }

@app.get("/time")
def last_time(age: int,die_age: int = 100):
    return {"end_time":die_age - age }

@app.get("/older")
def older(befor_age: int):
    if befor_age ==120:
        now_age = 0
    else:
        now_age = befor_age + 1
    return{"now_age":now_age}

