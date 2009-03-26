"""hooks/on_validation

on_validation is triggered any time you save. Here you can implement a read
only table...

try changing something and then saving.

"""

class Film(SqlMask):
    def on_validation(self):
        from sqlkit.exc import ValidationError
        
        raise ValidationError("I don't want you to change anything!!!")

t = Film(class_=model.Movie, dbproxy=db, )

t.reload()

