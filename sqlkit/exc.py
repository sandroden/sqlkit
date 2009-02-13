from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlkit import _

class FieldNotInLayout(Exception): pass
class FieldValueNotSet(Exception): pass
class NotHandledField(Exception): pass
class NotHandledDefault(Exception): pass

class MissingPrimaryKey(Exception): pass

class NoSyncError(Exception): pass
class SyncNotAvailable(Exception): pass
class MissingEngine(Exception): pass
class ValidationError(Exception): pass
class NotNullableFieldError(ValidationError):
    def __init__(self, field_name, message=None):
        self.field_name = field_name
        self.message = message or _("field %s cannot be NULL") % field_name
    
class InvalidValue(ValidationError):
    def __init__(self, field_name, value, message=None):
        self.field_name = field_name
        self.value = value
        self.message = message or _('field %s cannot have value %s') % (
            field_name, value)
    
class CommitError(ValidationError): pass
class CancelledAction(Exception): pass

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass
class UnhandledMultipleForeignkeys(Exception): pass

