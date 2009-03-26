"""hooks/on_completion

on_completion is triggered any time you choose from a completion
"""

class Film(SqlMask):
    def on_completion__director_id(self, field_name, obj):
        print vars(obj)
        print "Was this film directed by %s?" % obj['last_name']


t = Film(class_=model.Movie, dbproxy=db, )

t.reload()

