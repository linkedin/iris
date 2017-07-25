# 2016-01-25 -- v1.2.0

Add Bitcode markers.

# 2016-01-25 -- v1.1.3

- Bug fixes.

# 2015-12-08 -- v1.1.2

- Bug fixes.
- Fix dSYM warnings.

# 2015-10-21 -- v1.1.1

- Adds analytics support.
- Bug fixes.

# 2015-10-8 -- v1.1.0

- `[GCMService appDidReceiveMessage:]` now returns `BOOL` to signify if the
  message has already been received before.
- Fixes deleting old GCM registrations and topic subscriptions on app deletion
  and reinstall.
- Removes usage of clang modules for ObjC++ support.
- `GCMReceiverDelegate` protocol methods are now **optional**.
- Add `useNewRemoteNotificationCallback` property in `GCMConfig` to use new
  iOS8+ notification callback i.e.
  `application:didReceiveRemoteNotification:fetchCompletionHandler:`.
- Add better error reporting.
- Fix some compiler warnings.
- Bug fixes.
