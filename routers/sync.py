from fastapi import APIRouter
import requests
from tortoise.transactions import in_transaction
from routers.zk_connection import conn
import pickle

import os
import shutil

from models.db import Institute, Student, StudentInstallment, Installment, Attendance, StudentAttendance, Users, TemporaryDelete, TemporaryPatch


sync_router = APIRouter()

HOST = "http://127.0.0.1:8081"


async def get_fingerprints() -> list:
    conn.clear_data()
    result_list = []
    with open(os.path.join(
            os.getenv('LOCALAPPDATA'), 'ams', 'users_finger.pk'), "rb") as df:
        result_list = pickle.load(df)
    for user_finger in result_list:
        conn.set_user(uid=user_finger["user"].uid,
                      name=user_finger["user"].name, user_id=user_finger["user"].user_id)
        conn.save_user_template(user_finger["user"], user_finger["finger"])
    return result_list

# dob
# phone
# qr
# note
# photo
# banned
# institute


async def get_users() -> list:
    users = await Users.filter(sync_state=0).all()
    result_list = []
    for user in users:
        result_json = {"password": user.password, "username": user.username, "unique_id": user.unique_id,
                       "super": user.super,
                       "name": user.name}
        result_list.append(result_json)
    return result_list


def unzip_dir(filename, out_zip):
    shutil.unpack_archive(filename, out_zip, 'zip')


async def get_del() -> dict:
    all_deleted = await TemporaryDelete.filter(sync_state=0).all()
    unique_id_attendance = []
    unique_id_student_attendance = []
    for deleted in all_deleted:
        if deleted.model_id == 6:
            unique_id_attendance.append(deleted.unique_id)
        elif deleted.model_id == 7:
            unique_id_student_attendance.append(deleted.unique_id)
        await TemporaryDelete.filter(id=deleted.id).update(sync_state=1)
    return {
        "unique_id_attendance": unique_id_attendance,
        "unique_id_student_attendance": unique_id_student_attendance
    }


async def get_edits() -> tuple:
    tp = await TemporaryPatch.filter(sync_state=0).all()
    users = []
    attendance = []
    student_attendance = []
    for item in tp:
        if item.model_id == 4:
            users.append(item.unique_id)
        elif item.model_id == 6:
            attendance.append(item.unique_id)
        elif item.model_id == 7:
            student_attendance.append(item.unique_id)

    return users, attendance, student_attendance


def student_json(student) -> dict:
    institute_id = None
    if student.institute:
        institute_id = student.institute.id
    return {"name": student.name,
            "qr": student.qr,
            "photo": student.photo,
            "institute_id": institute_id,
            "dob": student.dob,
            "banned": student.banned,
            "note": student.note,
            "unique_id": student.unique_id}


async def get_all():
    installments_req = requests.get(f'{HOST}/installments')
    installments = await Installment.all().values('unique_id')
    installments = [n['unique_id'] for n in installments]
    installments_req = installments_req.json()
    installments_req = installments_req['installments']
    for installment in installments_req:
        if installment['unique_id'] not in installments:
            async with in_transaction() as conn:
                new = Installment(id=installment['id'], name=installment['name'], date=installment['date'], unique_id=installment['unique_id'],
                                  sync_state=1)
                await new.save(using_db=conn)
        elif installment['unique_id'] in installments and installment['delete_state'] == 0 and installment['patch_state'] == 1:
            await Installment.filter(unique_id=installment['unique_id']).update(name=installment['name'],
                                                                                date=installment["date"],
                                                                                sync_state=1)

    institutes_req = requests.get(f'{HOST}/institutes')
    institutes = await Institute.all().values('name')
    institutes = [n['name'] for n in institutes]
    institutes_req = institutes_req.json()
    institutes_req = institutes_req['institutes']
    for institute in institutes_req:
        if institute['name'] not in institutes:
            async with in_transaction() as conn:
                new = Institute(id=institute['id'], name=institute['name'])
                await new.save(using_db=conn)
    students_req = requests.get(f'{HOST}/students')
    students = await Student.all().values('unique_id')
    students = [n['unique_id'] for n in students]
    student_req = students_req.json()
    student_req = student_req['students']
    for student in student_req:
        if student['unique_id'] in students and student['delete_state'] == 1:
            await Student.filter(unique_id=student['unique_id']).delete()
        elif student['unique_id'] not in students and student['delete_state'] == 0:
            async with in_transaction() as conn:
                new = Student(name=student['name'],
                              institute_id=student['institute_id'],
                              phone=student['first_phone'],
                              note=student['note'],
                              qr=student["qr"],
                              photo=student["photo"],
                              dob=student["dob"],
                              banned=student["banned"],
                              unique_id=student['unique_id'], sync_state=1)
                await new.save(using_db=conn)
        elif student['unique_id'] in students and student['delete_state'] == 0 and student['patch_state'] == 1:
            await Student.filter(unique_id=student['unique_id']).update(name=student['name'],
                                                                        institute_id=student['institute_id'],
                                                                        phone=student['first_phone'],
                                                                        note=student['note'],
                                                                        qr=student["qr"],
                                                                        photo=student["photo"],
                                                                        dob=student["dob"],
                                                                        banned=student["banned"],
                                                                        sync_state=1)
    users_auth_req = requests.get(f'{HOST}/users')
    users_auth_req = users_auth_req.json()
    users_auth_req = users_auth_req['users']
    users = await Users.all().values('unique_id')
    users = [n['unique_id'] for n in users]
    for user in users_auth_req:
        if user['unique_id'] in users and user['delete_state'] == 1:
            await Users.filter(unique_id=user['unique_id']).delete()
        elif user['unique_id'] not in users and user['delete_state'] == 0:
            async with in_transaction() as conn:
                new = Users(username=user['username'], password=user['password'], unique_id=user['unique_id'], super=user["super"],
                            sync_state=1, name=user['name'])
                await new.save(using_db=conn)

        elif user['unique_id'] in users and user['delete_state'] == 0 and user['patch_state'] == 1:
            await Users.filter(unique_id=user['unique_id']).update(sync_state=1, username=user['username'], super=user["super"],
                                                                   password=user['password'], name=user['name'])
    student_installments_req = requests.get(f'{HOST}/student_installment')
    student_installments = await StudentInstallment.all().values('unique_id')
    student_installments_req = student_installments_req.json()
    student_installments = [n['unique_id'] for n in student_installments]
    reqs = student_installments_req['students_installments']
    for req in reqs:
        if req['unique_id'] in student_installments and req['delete_state'] == 1:
            await StudentInstallment.filter(unique_id=req['unique_id']).delete()
        if req['unique_id'] not in student_installments and req['delete_state'] == 0:
            stu = await Student.filter(unique_id=req['_student']['unique_id']).first()
            install = await Installment.filter(unique_id=req['_installment']['unique_id']).first()
            if stu is not None:
                async with in_transaction() as conn:
                    new = StudentInstallment(unique_id=req['unique_id'], sync_state=1,
                                             installment_id=install.id, student_id=stu.id, received=req['received'],)
                    await new.save(using_db=conn)
        if req['unique_id'] in student_installments and req['delete_state'] == 0 and req['patch_state'] == 1:
            stu = await Student.filter(unique_id=req['_student']['unique_id']).first()
            install = await Installment.filter(unique_id=req['_installment']['unique_id']).first()
            if stu is not None:
                await StudentInstallment.filter(unique_id=req['unique_id']).update(sync_state=1,
                                                                                   installment_id=install.id,
                                                                                   student_id=stu.id,
                                                                                   received=req['received'])

    attendance_req = requests.get(f'{HOST}/attendance')
    attendances = await Attendance.all().values('unique_id')
    attendances = [n['unique_id'] for n in attendances]
    attendance_req = attendance_req.json()
    attendance_req = attendance_req['attendance']
    for attendance in attendance_req:
        if attendance['unique_id'] not in attendances:
            async with in_transaction() as conn:
                new = Attendance(date=attendance['date'], unique_id=attendance['unique_id'], institute_id=attendance['institute_id'],
                                 sync_state=1)
                await new.save(using_db=conn)

    student_attendance_req = requests.get(f'{HOST}/student-attendance')
    student_attendance = await StudentAttendance.all().values('unique_id')
    student_attendance_req = student_attendance_req.json()
    student_attendance = [n['unique_id'] for n in student_attendance]
    reqs = student_attendance_req['students_attendance']
    for req in reqs:
        if req['unique_id'] in student_attendance and req['delete_state'] == 1:
            await StudentAttendance.filter(unique_id=req['unique_id']).delete()
        if req['unique_id'] not in student_attendance and req['delete_state'] == 0:
            stu = await Student.filter(unique_id=req['_student']['unique_id']).first()
            attendance = await Attendance.filter(unique_id=req['_attendance']['unique_id']).first()
            if stu is not None:
                async with in_transaction() as conn:
                    new = StudentAttendance(unique_id=req['unique_id'], sync_state=1, attended=req['attended'],
                                            attendance_id=attendance.id, student_id=stu.id, time=req['time'])
                    await new.save(using_db=conn)
        if req['unique_id'] in student_attendance and req['delete_state'] == 0 and req['patch_state'] == 1:
            stu = await Student.filter(unique_id=req['_student']['unique_id']).first()
            attendance = await Attendance.filter(unique_id=req['_attendance']['unique_id']).first()
            if stu is not None:
                await StudentAttendance.filter(unique_id=req['unique_id']).update(sync_state=1,
                                                                                  attended=req['attended'],
                                                                                  attendance_id=attendance.id,
                                                                                  student_id=stu.id,
                                                                                  time=req['time'])


@sync_router.get('/sync')
async def sync():

    with requests.get(f"{HOST}/qr", stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(os.getenv('LOCALAPPDATA'), 'ams', 'qr.zip'), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    with requests.get(f"{HOST}/images", stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(os.getenv('LOCALAPPDATA'), 'ams', 'images.zip'), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    with requests.get(f"{HOST}/fingerprints", stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(os.getenv('LOCALAPPDATA'), 'ams', 'users_finger.pk'), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    await get_fingerprints()
    path_qr = os.path.join(os.getenv('LOCALAPPDATA'), 'ams', 'qr')
    unzip_dir(os.path.join(os.getenv('LOCALAPPDATA'),
              'ims', 'qr' + ".zip"), path_qr)
    path_images = os.path.join(os.getenv('LOCALAPPDATA'), 'ams', 'images')
    unzip_dir(os.path.join(os.getenv('LOCALAPPDATA'),
              'ims', 'images' + ".zip"), path_images)

    attendances = await Attendance.filter(sync_state=0).prefetch_related().all()
    for attendance in attendances:
        req = requests.post(f"{HOST}/attendance",
                            json={"date": str(attendance.date),
                                  "institute_id": attendance.institute_id, "unique_id": attendance.unique_id})
        if req.status_code == 200:
            await Attendance.filter(id=attendance.id).update(sync_state=1)

    students = await Student.all().prefetch_related('institute')

    for student_attend in students:
        stu_attend = await StudentAttendance.filter(student_id=student_attend.id, sync_state=0).all(). \
            prefetch_related(
            'attendance')
        for attend in stu_attend:
            json_attend = {"time": attend.time, "unique_id": attend.unique_id,
                           "attended": attend.attended,
                           "attendance_unique_id": attend.attendance.unique_id,
                           "student_unique_id": student_attend.unique_id}
            req = requests.post(
                f'{HOST}/student-attendance', json=json_attend)
            if req.status_code == 200:
                await StudentAttendance.filter(id=attend.id).update(sync_state=1)

    all_del = await get_del()
    req = requests.post(f'{HOST}/del', json=all_del)
    users_patch, attendances_patch, students_attendance_patch = await get_edits()

    # for user_auth in users_patch:
    #     user = await Users.filter(unique_id=user_auth).first()
    #     user_json = {
    #         "name": user.name,
    #         "username": user.username,
    #         "password": user.password,
    #         "super": user.super,
    #         "unique_id": user.unique_id
    #     }
    #     req = requests.post(f'{HOST}/users', json=user_json)
    #     if req.status_code == 200:
    #         await TemporaryPatch.filter(unique_id=user.unique_id).update(sync_state=1)

    for attendance_patch in attendances_patch:
        atte = await Attendance.filter(unique_id=attendance_patch).first()
        attendance_json = {"date": atte.date, "unique_id": atte.unique_id,
                           "institute_id": atte.institute_id
                           }
        req = requests.post(f'{HOST}/attendance', json=attendance_json)
        if req.status_code == 200:
            await TemporaryPatch.filter(unique_id=atte.unique_id).update(sync_state=1)

    for student_attendance_patch in students_attendance_patch:
        attend_patch = await StudentAttendance.filter(unique_id=student_attendance_patch).first().prefetch_related(
            'student', 'attendance')
        data_patch = {"time": str(attend_patch.time), "attended": attend_patch.attended,
                      "unique_id": attend_patch.unique_id,
                      "attendance_unique_id": attend_patch.attendance.unique_id,
                      "student_unique_id": attend_patch.student.unique_id, "patch": True}
        req = requests.post(f'{HOST}/student-attendance', json=data_patch)
        if req.status_code == 200:
            await TemporaryPatch.filter(unique_id=attend_patch.unique_id).update(sync_state=1)

    await get_all()
    return {
        "success": True
    }
