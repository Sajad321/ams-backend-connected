from tortoise.models import Model
from tortoise import fields


class Users(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)
    username = fields.CharField(max_length=100, unique=True)
    password = fields.TextField()
    super = fields.IntField(default=0)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Users"


class Student(Model):
    id = fields.IntField(pk=True, unique=True)
    name = fields.TextField(null=True)
    dob = fields.TextField(null=True)
    phone = fields.IntField(null=True)
    qr = fields.CharField(max_length=100, unique=True, null=True)
    note = fields.TextField(null=True)
    photo = fields.TextField(null=True)
    banned = fields.IntField(null=True, default=0)
    institute = fields.ForeignKeyField('models.Institute', null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Student"


class Institute(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)

    class Meta:
        table = "Institute"


class Attendance(Model):
    id = fields.IntField(pk=True)
    date = fields.TextField(null=True)
    institute = fields.ForeignKeyField('models.Institute', null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Attendance"


class StudentAttendance(Model):
    id = fields.IntField(pk=True)
    student = fields.ForeignKeyField('models.Student', null=True)
    attendance = fields.ForeignKeyField('models.Attendance', null=True)
    attended = fields.IntField(default=0)
    time = fields.TextField(null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Student_Attendance"


class Installment(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField(null=True)
    date = fields.TextField(null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Installment"


class StudentInstallment(Model):
    id = fields.IntField(pk=True)
    installment = fields.ForeignKeyField('models.Installment', null=True)
    student = fields.ForeignKeyField('models.Student', null=True)
    received = fields.IntField(default=0, null=True)
    unique_id = fields.TextField()
    sync_state = fields.IntField(default=0)  # 0 offline, 1 synced

    class Meta:
        table = "Student_Installment"


class TemporaryDelete(Model):
    id = fields.IntField(pk=True)
    unique_id = fields.TextField()
    model_id = fields.IntField()
    sync_state = fields.IntField(default=0)
    ''' 
    model_id = {"Students": 1, "student_installment": 3, "users": 4, "installments": 5, "attendance": 6, "student_attendance": 7}
    '''


class TemporaryPatch(Model):
    id = fields.IntField(pk=True)
    unique_id = fields.TextField()
    model_id = fields.IntField()
    sync_state = fields.IntField(default=0)
    ''' 
    model_id = {"Students": 1, "student_installment": 3, "users": 4, "installments": 5, "attendance": 6, "student_attendance": 7}
    '''
