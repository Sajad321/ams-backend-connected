from fastapi import APIRouter
from models import session, engine, Base, Institute, Student, Attendance, Student_Attendance, Batch, Student_Installment
from typing import Optional

router = APIRouter()


# insert Attendance
@router.post('/attendance')
def post_attendance(date, batch_id, institute_id):
    new = Attendance(date=date, batch_id=batch_id, institute_id=institute_id)
    Attendance.insert(new)
    query = session.query(Student).filter_by(batch_id=batch_id, institute_id=institute_id).all()
    for stu in [qu.students() for qu in query]:
        new_attend = Student_Attendance(student_id=stu['id'], attendance_id=new.id)
        Student_Attendance.insert(new_attend)
    return {
        "success": True
    }


# To change attendance
@router.patch('/attendance')
def patch_attendance(_id: int, date: str, batch_id: int, institute_id: int):
    new = session.query(Attendance).get(_id)
    new.date = date
    new.batch_id = batch_id
    new.institute_id = institute_id
    Attendance.update(new)
    return {
        "success": True
    }


# insert students attendance
@router.post('/students-attendance')
def post_student_attendance(attendance_id, student_id, attend: int):
    new = Student_Attendance(attendance_id=attendance_id, student_id=student_id, attended=attend)
    Student_Attendance.insert(new)
    return {
        "success": True
    }


# get student attendance by institute id
@router.get('/students-attendance-institute-bid')
def students_attendance_institute(institute_id: int):
    query = session.query(Student).filter_by(institute_id=institute_id).all()
    students = [record.students() for record in query]
    new_attend = {}
    enlist = []
    for stu in students:
        attendance = session.query(Student_Attendance).filter_by(student_id=stu['id']).all()
        for attend in [att.format() for att in attendance]:
            new_attend['student_attendance_id'] = attend['id']
            new_attend['attended'] = attend['attended']
            enlist.append(new_attend)
            new_attend = {}
        stu.update({"students_attendace": enlist})
        enlist = []

    return students


# To change Student Attendance
@router.patch('/students_attendance')
def students_attendance(_id: int, student_id: int, attend_id: int, attended: int):
    new = session.query(Student_Attendance).get(_id)
    new.student_id = student_id
    new.attendance_id = attend_id
    new.attended = attended
    Student_Attendance.update(new)
    return {
        "success": True
    }
