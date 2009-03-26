"""hooks/on_field_validation

you can set hooks on single field validation. It will be called from within
the field 


"""
from sqlkit.exc import ValidationError

class Film(SqlMask):

    def on_field_validation__year(self, field_name, field_value, field):
        if field_value > 2020:
            raise ValidationError("Hei: how can you know the future!")


lay = """
   title
   year
   director_id
   m2m=genres -
   """

t = Film(class_=model.Movie, layout=lay, label_map={'genres.name':'genres'},
         dbproxy=db, )

t.reload()

