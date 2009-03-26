"""hooks/on_validation - related

you can also change a related validation be sure you understand when you
have to check a sqlkitget or a related one.  If you want to prevent a change
in a related table where you cannot edit (as is the genres table), you must
set the check on the validation of attribute 'genres' of the main Mask.

In the contrary the completion on genres take place in the related table, so that you need to add __genres__ to the name of the method

"""
from sqlkit.exc import ValidationError
from sqlkit.db.utils import get_differences

class Film(SqlMask):
    def on_field_validation__genres(self, field_name, field_value, field):
        for field_name, old, new in get_differences(self.current):
            if field_name == 'genres':
                raise ValidationError("I don't want you to change the genre!!!")
        
    def on_completion__genres__name(self, field_name, obj):
        print "No, please, don't change the genres..."


lay = """
   title
   year
   director_id
   m2m=genres -
   """

t = Film(class_=model.Movie, layout=lay, label_map={'genres.name':'genres'},
         dbproxy=db, )

t.reload()

