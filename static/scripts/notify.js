if (!Notify.needsPermission) {
    doNotification();
} else if (Notify.isSupported()) {
    Notify.requestPermission(onPermissionGranted, onPermissionDenied);
}

function onPermissionGranted() {
    console.log('Permission has been granted by the user');
    doNotification();
}

function onPermissionDenied() {
    console.warn('Permission has been denied by the user');
}

function onNotifyShow() {
    console.log('notification was shown!');
}
