# this is python3 testing only.
# so let's make sure this is not executed on python2
# that sucks *so* much.
mock_available = False
try:
    # python 3.something
    from unittest.mock import patch, call, MagicMock
    mock_available = True
except ImportError:
    try:
        # python < 3.something with mock installed
        from mock import patch, call
        mock_available = True
    except ImportError:
        pass
# did I mention this sucks?
