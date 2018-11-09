var notify = require('notifyjs');

function showNotification(text, body) {
  if (!notify.needsPermission) {
    doNotification(text,body);
} else if (notify.isSupported()) {
    notify.requestPermission(onPermissionGranted, onPermissionDenied);
} else if (!notify.isSupported()) {
    console.warn('Notifications are not supported in this browser');
}

}
function onPermissionGranted() {
    console.log('Permission has been granted by the user');
}

function onPermissionDenied() {
    console.warn('Permission has been denied by the user');
}
function onNotifyShow() {
    console.log('Notification Shown');
}

function doNotification(text, body) {
    var n = new notify(text, {
                body: body,
                notifyShow: onNotifyShow 
            });

    n.show();
}

exports.showNotification = showNotification;
