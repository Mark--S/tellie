import sys
import couchdb


def assign_document(doc):
    """Return a the document type depending on the type field.
    """
    try:
        if doc["type"] == "channel":
            return ChannelDocument(doc)
        elif doc["type"] == "pattern":
            return PatternDocument(doc)
        elif doc["type"] == "run":
            return RunDocument(doc)
        else:
            sys.stderr.write("Unknown document type\n")
            return None
    except KeyError, e:
        sys.stderr.write("Document does not contain 'type' parameter\n")
        raise


class Document(couchdb.Document):
    """Base class for couchdb TELLIE documents.
    """
    def __init__(self, data):
        super(Document, self).__init__(data)
        self._unique_view = None

    def unique_view(self):
        """Get the view parameters to check if this document exists on the db.
        """
        view_key = []
        for key in self._unique_key:
            # Ignore unicode stuff for now
            try:
                view_key.append(self[key])
            except KeyError:
                sys.stderr.write("Document is missing a required key: %s\n" % dict(self))
                raise
        return (self._unique_view, view_key)


class ChannelDocument(Document):
    """Class for channel documents.
    """
    def __init__(self, data):
        super(ChannelDocument, self).__init__(data)
        self._unique_view = "_design/channels/_view/channel_by_number"
        self._unique_key = ["channel", "pass"]


class PatternDocument(Document):
    """Class for pattern documents.
    """
    def __init__(self, data):
        super(PatternDocument, self).__init__(data)
        self._unique_view = "_design/patterns/_view/pattern_by_name"
        self._unique_key = ["pattern", "pass"]


class RunDocument(Document):
    """Class for run documents.
    """
    def __init__(self, data):
        super(RunDocument, self).__init__(data)
        self._unique_view = "_design/runs/_view/run_by_name"
        self._unique_key = ["run", "pass"]


