from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class FieldNotInLayout(Exception): pass
class FieldValueNotSet(Exception): pass
class NotHandledField(Exception): pass
class NotHandledDefault(Exception): pass

class NoSyncError(Exception): pass
class SyncNotAvailable(Exception): pass
class MissingEngine(Exception): pass
class ValidationError(Exception): pass
class CommitError(ValidationError): pass
class CancelledAction(Exception): pass

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass
class UnhandledMultipleForeignkeys(Exception): pass

