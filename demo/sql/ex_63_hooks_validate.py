"""hooks/on_validation - related

you can also change a related validation


"""

class Film(SqlMask):
    def on_validation__genres(self, field_name, obj):
        from sqlkit.exc import ValidationError
        raise ValidationError("I don't want you to change the genre!!!")
        
    def on_completion__genres__name(self, field_name, obj):
        print "No, please, don't change the genres..."


lay = """
   title
   director_id
   m2m=genres -
   """

t = Film(class_=model.Movie, layout=lay, label_map={'genres.name':'genres'},
         dbproxy=db, )

t.reload()

