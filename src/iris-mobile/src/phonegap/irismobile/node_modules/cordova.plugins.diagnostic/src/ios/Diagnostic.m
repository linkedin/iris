/*
 *  Diagnostic.h
 *  Plugin diagnostic
 *
 *  Copyright (c) 2015 Working Edge Ltd.
 *  Copyright (c) 2012 AVANTIC ESTUDIO DE INGENIEROS
 */

#import "Diagnostic.h"

@interface Diagnostic()

#if defined(__IPHONE_9_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_9_0
@property (nonatomic, retain) CNContactStore* contactStore;
#endif

@end


@implementation Diagnostic

#if __IPHONE_OS_VERSION_MAX_ALLOWED < __IPHONE_9_0
ABAddressBookRef _addressBook;
#endif
- (void)pluginInitialize {
    
    [super pluginInitialize];
    
    self.locationRequestCallbackId = nil;
    self.currentLocationAuthorizationStatus = nil;
    self.locationManager = [[CLLocationManager alloc] init];
    self.locationManager.delegate = self;
    
    self.bluetoothManager = [[CBCentralManager alloc]
                             initWithDelegate:self
                             queue:dispatch_get_main_queue()
                             options:@{CBCentralManagerOptionShowPowerAlertKey: @(NO)}];
    [self centralManagerDidUpdateState:self.bluetoothManager]; // Show initial state
    self.contactStore = [[CNContactStore alloc] init];
    self.motionManager = [[CMMotionActivityManager alloc] init];
    self.motionActivityQueue = [[NSOperationQueue alloc] init];
}

/********************************/
#pragma mark - Plugin API
/********************************/

#pragma mark - Location
- (void) isLocationAvailable: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[CLLocationManager locationServicesEnabled] && [self isLocationAuthorized] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isLocationEnabled: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[CLLocationManager locationServicesEnabled] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}


- (void) isLocationAuthorized: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[self isLocationAuthorized] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) getLocationAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status = [self getLocationAuthorizationStatusAsString:[CLLocationManager authorizationStatus]];
        NSLog(@"%@",[NSString stringWithFormat:@"Location authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestLocationAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        if ([CLLocationManager instancesRespondToSelector:@selector(requestWhenInUseAuthorization)])
        {
            BOOL always = [[command argumentAtIndex:0] boolValue];
            if(always){
                NSAssert([[[NSBundle mainBundle] infoDictionary] valueForKey:@"NSLocationAlwaysUsageDescription"], @"For iOS 8 and above, your app must have a value for NSLocationAlwaysUsageDescription in its Info.plist");
                [self.locationManager requestAlwaysAuthorization];
                NSLog(@"Requesting location authorization: always");
            }else{
                NSAssert([[[NSBundle mainBundle] infoDictionary] valueForKey:@"NSLocationWhenInUseUsageDescription"], @"For iOS 8 and above, your app must have a value for NSLocationWhenInUseUsageDescription in its Info.plist");
                [self.locationManager requestWhenInUseAuthorization];
                NSLog(@"Requesting location authorization: when in use");
            }
        }
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
    self.locationRequestCallbackId = command.callbackId;
    CDVPluginResult* pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_NO_RESULT];
    [pluginResult setKeepCallback:[NSNumber numberWithBool:YES]];
    [self sendPluginResult:pluginResult :command];
}

#pragma mark - Camera
- (void) isCameraAvailable: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[self isCameraPresent] && [self isCameraAuthorized] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isCameraPresent: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[self isCameraPresent] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isCameraAuthorized: (CDVInvokedUrlCommand*)command
{    @try {
    [self sendPluginResultBool:[self isCameraAuthorized] :command];
}
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) getCameraAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status;
        AVAuthorizationStatus authStatus = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeVideo];
        
        if(authStatus == AVAuthorizationStatusDenied || authStatus == AVAuthorizationStatusRestricted){
            status = @"denied";
        }else if(authStatus == AVAuthorizationStatusNotDetermined){
            status = @"not_determined";
        }else if(authStatus == AVAuthorizationStatusAuthorized){
            status = @"authorized";
        }
        NSLog(@"%@",[NSString stringWithFormat:@"Camera authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestCameraAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        [AVCaptureDevice requestAccessForMediaType:AVMediaTypeVideo completionHandler:^(BOOL granted) {
            [self sendPluginResultBool:granted :command];
        }];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isCameraRollAuthorized: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[[self getCameraRollAuthorizationStatus]  isEqual: @"authorized"] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) getCameraRollAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status = [self getCameraRollAuthorizationStatus];
        NSLog(@"%@",[NSString stringWithFormat:@"Camera Roll authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestCameraRollAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        [PHPhotoLibrary requestAuthorization:^(PHAuthorizationStatus authStatus) {
            NSString* status = [self getCameraRollAuthorizationStatusAsString:authStatus];
            [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
        }];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark -  Wifi
- (void) isWifiAvailable: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[self connectedToWifi] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isWifiEnabled: (CDVInvokedUrlCommand*)command
{
    @try {
        [self sendPluginResultBool:[self isWifiEnabled] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (BOOL) isWifiEnabled {

    NSCountedSet * cset = [NSCountedSet new];

    struct ifaddrs *interfaces;

    if( ! getifaddrs(&interfaces) ) {
        for( struct ifaddrs *interface = interfaces; interface; interface = interface->ifa_next) {
            if ( (interface->ifa_flags & IFF_UP) == IFF_UP ) {
                [cset addObject:[NSString stringWithUTF8String:interface->ifa_name]];
            }
        }
    }

    return [cset countForObject:@"awdl0"] > 1 ? YES : NO;
}


#pragma mark - Bluetooth

- (void) isBluetoothAvailable: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* state = [self getBluetoothState];
        bool bluetoothEnabled;
        if([state  isEqual: @"powered_on"]){
            bluetoothEnabled = true;
        }else{
            bluetoothEnabled = false;
        }
        [self sendPluginResultBool:bluetoothEnabled :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) getBluetoothState: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* state = [self getBluetoothState];
        NSLog(@"%@",[NSString stringWithFormat:@"Bluetooth state is: %@", state]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:state] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
    
}

- (void) requestBluetoothAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* state = [self getBluetoothState];
        
        if([state isEqual: @"unauthorized"]){
            /*
             When the application requests to start scanning for bluetooth devices that is when the user is presented with a consent dialog.
             */
            NSLog(@"Requesting bluetooth authorization");
            [self.bluetoothManager scanForPeripheralsWithServices:nil options:nil];
            [self.bluetoothManager stopScan];
        }else{
            NSLog(@"Bluetooth authorization is already granted");
        }
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark -  Settings
- (void) switchToSettings: (CDVInvokedUrlCommand*)command
{
    @try {
        if (UIApplicationOpenSettingsURLString != nil ){
            if ([[UIApplication sharedApplication] respondsToSelector:@selector(openURL:options:completionHandler:)]) {
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
                [[UIApplication sharedApplication] openURL:[NSURL URLWithString: UIApplicationOpenSettingsURLString] options:@{} completionHandler:^(BOOL success) {
                    if (success) {
                        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK] :command];
                    }else{
                        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR] :command];
                    }
                }];
#endif
            }else{
                [[UIApplication sharedApplication] openURL: [NSURL URLWithString: UIApplicationOpenSettingsURLString]];
                [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK] :command];
            }
        }else{
            [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR messageAsString:@"Not supported below iOS 8"]:command];
        }
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Audio
- (void) isMicrophoneAuthorized: (CDVInvokedUrlCommand*)command
{
    CDVPluginResult* pluginResult;
    @try {
#ifdef __IPHONE_8_0
        AVAudioSessionRecordPermission recordPermission = [AVAudioSession sharedInstance].recordPermission;
        
        if(recordPermission == AVAudioSessionRecordPermissionGranted) {
            pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsInt:1];
        }
        else {
            pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsInt:0];
        }
        [self sendPluginResultBool:recordPermission == AVAudioSessionRecordPermissionGranted :command];
#else
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR messageAsString:@"Only supported on iOS 8 and higher"]:command];
#endif
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    };
}

- (void) getMicrophoneAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
#ifdef __IPHONE_8_0
        NSString* status;
        AVAudioSessionRecordPermission recordPermission = [AVAudioSession sharedInstance].recordPermission;
        switch(recordPermission){
            case AVAudioSessionRecordPermissionDenied:
                status = @"denied";
                break;
            case AVAudioSessionRecordPermissionGranted:
                status = @"authorized";
                break;
            case AVAudioSessionRecordPermissionUndetermined:
                status = @"not_determined";
                break;
        }
        
        NSLog(@"%@",[NSString stringWithFormat:@"Microphone authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
#else
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR messageAsString:@"Only supported on iOS 8 and higher"]:command];
#endif
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestMicrophoneAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        [[AVAudioSession sharedInstance] requestRecordPermission:^(BOOL granted) {
            NSLog(@"HAs access to microphone: %d", granted);
            [self sendPluginResultBool:granted :command];
        }];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Remote (Push) Notifications
- (void) isRemoteNotificationsEnabled: (CDVInvokedUrlCommand*)command
{
    @try {
        if ([[UIApplication sharedApplication] respondsToSelector:@selector(registerUserNotificationSettings:)]) {
            // iOS 8+
            if(NSClassFromString(@"UNUserNotificationCenter")) {
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
                // iOS 10+
                UNUserNotificationCenter* center = [UNUserNotificationCenter currentNotificationCenter];
                [center getNotificationSettingsWithCompletionHandler:^(UNNotificationSettings * _Nonnull settings) {
                    BOOL userSettingEnabled = settings.authorizationStatus == UNAuthorizationStatusAuthorized;
                    [self isRemoteNotificationsEnabledResult:userSettingEnabled:command];
                }];
#endif
            } else{
                // iOS 8 & 9
                UIUserNotificationSettings *userNotificationSettings = [UIApplication sharedApplication].currentUserNotificationSettings;
                BOOL userSettingEnabled = userNotificationSettings.types != UIUserNotificationTypeNone;
                [self isRemoteNotificationsEnabledResult:userSettingEnabled:command];
            }
        } else {
            // iOS7 and below
#if __IPHONE_OS_VERSION_MAX_ALLOWED <= __IPHONE_7_0
            UIRemoteNotificationType enabledRemoteNotificationTypes = [UIApplication sharedApplication].enabledRemoteNotificationTypes;
            BOOL isEnabled = enabledRemoteNotificationTypes != UIRemoteNotificationTypeNone;
            [self sendPluginResultBool:isEnabled:command];
#endif
        }
        
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception:command];
    }
}
- (void) isRemoteNotificationsEnabledResult: (BOOL) userSettingEnabled : (CDVInvokedUrlCommand*)command
{
    // iOS 8+
    BOOL remoteNotificationsEnabled = [UIApplication sharedApplication].isRegisteredForRemoteNotifications;
    BOOL isEnabled = remoteNotificationsEnabled && userSettingEnabled;
    [self sendPluginResultBool:isEnabled:command];
}

- (void) getRemoteNotificationTypes: (CDVInvokedUrlCommand*)command
{
    @try {
        if ([[UIApplication sharedApplication] respondsToSelector:@selector(registerUserNotificationSettings:)]) {
            // iOS 8+
            if(NSClassFromString(@"UNUserNotificationCenter")) {
                // iOS 10+
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
                UNUserNotificationCenter* center = [UNUserNotificationCenter currentNotificationCenter];
                [center getNotificationSettingsWithCompletionHandler:^(UNNotificationSettings * _Nonnull settings) {
                    BOOL alertsEnabled = settings.alertSetting == UNNotificationSettingEnabled;
                    BOOL badgesEnabled = settings.badgeSetting == UNNotificationSettingEnabled;
                    BOOL soundsEnabled = settings.soundSetting == UNNotificationSettingEnabled;
                    BOOL noneEnabled = !alertsEnabled && !badgesEnabled && !soundsEnabled;
                    [self getRemoteNotificationTypesResult:command:noneEnabled:alertsEnabled:badgesEnabled:soundsEnabled];
                }];
#endif
            } else{
                // iOS 8 & 9
                UIUserNotificationSettings *userNotificationSettings = [UIApplication sharedApplication].currentUserNotificationSettings;
                BOOL noneEnabled = userNotificationSettings.types == UIUserNotificationTypeNone;
                BOOL alertsEnabled = userNotificationSettings.types & UIUserNotificationTypeAlert;
                BOOL badgesEnabled = userNotificationSettings.types & UIUserNotificationTypeBadge;
                BOOL soundsEnabled = userNotificationSettings.types & UIUserNotificationTypeSound;
                [self getRemoteNotificationTypesResult:command:noneEnabled:alertsEnabled:badgesEnabled:soundsEnabled];
            }
        } else {
            // iOS7 and below
#if __IPHONE_OS_VERSION_MAX_ALLOWED <= __IPHONE_7_0
            UIRemoteNotificationType enabledRemoteNotificationTypes = [UIApplication sharedApplication].enabledRemoteNotificationTypes;
            BOOL oneEnabled = enabledRemoteNotificationTypes == UIRemoteNotificationTypeNone;
            BOOL alertsEnabled = enabledRemoteNotificationTypes & UIRemoteNotificationTypeAlert;
            BOOL badgesEnabled = enabledRemoteNotificationTypes & UIRemoteNotificationTypeBadge;
            BOOL soundsEnabled = enabledRemoteNotificationTypes & UIRemoteNotificationTypeSound;
            [self getRemoteNotificationTypesResult:command:noneEnabled:alertsEnabled:badgesEnabled:soundsEnabled];
#endif
        }
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}
- (void) getRemoteNotificationTypesResult: (CDVInvokedUrlCommand*)command :(BOOL)noneEnabled :(BOOL)alertsEnabled :(BOOL)badgesEnabled :(BOOL)soundsEnabled
{
    // iOS 8+
    NSMutableDictionary* types = [[NSMutableDictionary alloc]init];
    if(alertsEnabled) {
        [types setValue:@"1" forKey:@"alert"];
    } else {
        [types setValue:@"0" forKey:@"alert"];
    }
    if(badgesEnabled) {
        [types setValue:@"1" forKey:@"badge"];
    } else {
        [types setValue:@"0" forKey:@"badge"];
    }
    if(soundsEnabled) {
        [types setValue:@"1" forKey:@"sound"];
    } else {;
        [types setValue:@"0" forKey:@"sound"];
    }
    [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:[self objectToJsonString:types]] :command];
}


- (void) isRegisteredForRemoteNotifications: (CDVInvokedUrlCommand*)command
{
    BOOL registered;
    @try {
        if ([[UIApplication sharedApplication] respondsToSelector:@selector(registerUserNotificationSettings:)]) {
            // iOS8+
#if defined(__IPHONE_8_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_8_0
            registered = [UIApplication sharedApplication].isRegisteredForRemoteNotifications;
#endif
        } else {
#if __IPHONE_OS_VERSION_MAX_ALLOWED <= __IPHONE_7_0
            // iOS7 and below
            UIRemoteNotificationType enabledRemoteNotificationTypes = [UIApplication sharedApplication].enabledRemoteNotificationTypes;
            registered = enabledRemoteNotificationTypes != UIRemoteNotificationTypeNone;
#endif
        }
        [self sendPluginResultBool:registered :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Address Book (Contacts)

- (void) getAddressBookAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status;
        
#if defined(__IPHONE_9_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_9_0
        CNAuthorizationStatus authStatus = [CNContactStore authorizationStatusForEntityType:CNEntityTypeContacts];
        if(authStatus == CNAuthorizationStatusDenied || authStatus == CNAuthorizationStatusRestricted){
            status = @"denied";
        }else if(authStatus == CNAuthorizationStatusNotDetermined){
            status = @"not_determined";
        }else if(authStatus == CNAuthorizationStatusAuthorized){
            status = @"authorized";
        }
#else
        ABAuthorizationStatus authStatus = ABAddressBookGetAuthorizationStatus();
        if(authStatus == kABAuthorizationStatusDenied || authStatus == kABAuthorizationStatusRestricted){
            status = @"denied";
        }else if(authStatus == kABAuthorizationStatusNotDetermined){
            status = @"not_determined";
        }else if(authStatus == kABAuthorizationStatusAuthorized){
            status = @"authorized";
        }
        
#endif
        
        NSLog(@"%@",[NSString stringWithFormat:@"Address book authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isAddressBookAuthorized: (CDVInvokedUrlCommand*)command
{
    @try {
        
#if defined(__IPHONE_9_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_9_0
        CNAuthorizationStatus authStatus = [CNContactStore authorizationStatusForEntityType:CNEntityTypeContacts];
        [self sendPluginResultBool:authStatus == CNAuthorizationStatusAuthorized :command];
#else
        ABAuthorizationStatus authStatus = ABAddressBookGetAuthorizationStatus();
        [self sendPluginResultBool:authStatus == kABAuthorizationStatusAuthorized :command];
#endif
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestAddressBookAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
#if __IPHONE_OS_VERSION_MAX_ALLOWED < __IPHONE_9_0
        ABAddressBookRequestAccessWithCompletion(self.addressBook, ^(bool granted, CFErrorRef error) {
            NSLog(@"Access request to address book: %d", granted);
            [self sendPluginResultBool:granted :command];
        });
        
#else
        [self.contactStore requestAccessForEntityType:CNEntityTypeContacts completionHandler:^(BOOL granted, NSError * _Nullable error) {
            if(error == nil) {
                NSLog(@"Access request to address book: %d", granted);
                [self sendPluginResultBool:granted :command];
            }
            else {
                [self sendPluginResultBool:FALSE :command];
            }
        }];
#endif
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Calendar Events

- (void) getCalendarAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status;
        
        EKAuthorizationStatus authStatus = [EKEventStore authorizationStatusForEntityType:EKEntityTypeEvent];
        
        if(authStatus == EKAuthorizationStatusDenied || authStatus == EKAuthorizationStatusRestricted){
            status = @"denied";
        }else if(authStatus == EKAuthorizationStatusNotDetermined){
            status = @"not_determined";
        }else if(authStatus == EKAuthorizationStatusAuthorized){
            status = @"authorized";
        }
        NSLog(@"%@",[NSString stringWithFormat:@"Calendar event authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isCalendarAuthorized: (CDVInvokedUrlCommand*)command
{
    @try {
        EKAuthorizationStatus authStatus = [EKEventStore authorizationStatusForEntityType:EKEntityTypeEvent];
        [self sendPluginResultBool:authStatus == EKAuthorizationStatusAuthorized:command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestCalendarAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        
        if (!self.eventStore) {
            self.eventStore = [EKEventStore new];
        }
        
        [self.eventStore requestAccessToEntityType:EKEntityTypeEvent completion:^(BOOL granted, NSError *error) {
            NSLog(@"Access request to calendar events: %d", granted);
            [self sendPluginResultBool:granted:command];
        }];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Reminder Events

- (void) getRemindersAuthorizationStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status;
        
        EKAuthorizationStatus authStatus = [EKEventStore authorizationStatusForEntityType:EKEntityTypeReminder];
        
        if(authStatus == EKAuthorizationStatusDenied || authStatus == EKAuthorizationStatusRestricted){
            status = @"denied";
        }else if(authStatus == EKAuthorizationStatusNotDetermined){
            status = @"not_determined";
        }else if(authStatus == EKAuthorizationStatusAuthorized){
            status = @"authorized";
        }
        NSLog(@"%@",[NSString stringWithFormat:@"Reminders authorization status is: %@", status]);
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isRemindersAuthorized: (CDVInvokedUrlCommand*)command
{
    @try {
        EKAuthorizationStatus authStatus = [EKEventStore authorizationStatusForEntityType:EKEntityTypeReminder];
        [self sendPluginResultBool:authStatus == EKAuthorizationStatusAuthorized:command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) requestRemindersAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        
        if (!self.eventStore) {
            self.eventStore = [EKEventStore new];
        }
        
        [self.eventStore requestAccessToEntityType:EKEntityTypeReminder completion:^(BOOL granted, NSError *error) {
            NSLog(@"Access request to reminders: %d", granted);
            [self sendPluginResultBool:granted:command];
        }];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Background refresh
- (void) getBackgroundRefreshStatus: (CDVInvokedUrlCommand*)command
{
    @try {
        NSString* status;
        
        if ([[UIApplication sharedApplication] backgroundRefreshStatus] == UIBackgroundRefreshStatusAvailable) {
            status = @"authorized";
            NSLog(@"Background updates are available for the app.");
        }else if([[UIApplication sharedApplication] backgroundRefreshStatus] == UIBackgroundRefreshStatusDenied){
            status = @"denied";
            NSLog(@"The user explicitly disabled background behavior for this app or for the whole system.");
        }else if([[UIApplication sharedApplication] backgroundRefreshStatus] == UIBackgroundRefreshStatusRestricted){
            status = @"restricted";
            NSLog(@"Background updates are unavailable and the user cannot enable them again. For example, this status can occur when parental controls are in effect for the current user.");
        }
        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

#pragma mark - Motion methods

- (void) isMotionAvailable:(CDVInvokedUrlCommand *)command
{
    @try {
        
        [self sendPluginResultBool:[self isMotionAvailable] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}

- (void) isMotionRequestOutcomeAvailable:(CDVInvokedUrlCommand *)command
{
    @try {
        
        [self sendPluginResultBool:[self isMotionRequestOutcomeAvailable] :command];
    }
    @catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}


- (void) requestAndCheckMotionAuthorization: (CDVInvokedUrlCommand*)command
{
    @try {
        if([self isMotionAvailable]){
            [self.motionManager startActivityUpdatesToQueue:self.motionActivityQueue withHandler:^(CMMotionActivity *activity) {
                @try {
                    [self.motionManager stopActivityUpdates];
                    if([self isMotionRequestOutcomeAvailable]){
                        CMPedometer* cmPedometer = [[CMPedometer alloc] init];
                        [cmPedometer queryPedometerDataFromDate:[NSDate date]
                             toDate:[NSDate date]
                        withHandler:^(CMPedometerData* data, NSError *error) {
                            @try {
                                NSString* status;
                                if (error != nil && error.code == CMErrorMotionActivityNotAuthorized) {
                                    status = @"denied";
                                }else if (error != nil && (
                                                           error.code == CMErrorMotionActivityNotEntitled
                                                           || error.code == CMErrorMotionActivityNotAvailable
                                                           )) {
                                    status = @"restricted";
                                }else{
                                    status = @"authorized";
                                }
                                
                                NSLog(@"Motion access is %@", status);
                                [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status] :command];
                            }@catch (NSException *exception) {
                                [self handlePluginException:exception :command];
                            }
                        }];
                    }else{
                        NSLog(@"Pedometer tracking not available on this device - cannot determine motion authorization status");
                        [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:@"not_determined"] :command];
                    }
                }@catch (NSException *exception) {
                    [self handlePluginException:exception :command];
                }
            }];
        }else{
            NSString* errMsg = @"Activity tracking not available on this device";
            NSLog(@"%@", errMsg);
            [self sendPluginResult:[CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR messageAsString:errMsg] :command];
        }
        

    }@catch (NSException *exception) {
        [self handlePluginException:exception :command];
    }
}
        

/********************************/
#pragma mark - Send results
/********************************/

- (void) sendPluginResult: (CDVPluginResult*)result :(CDVInvokedUrlCommand*)command
{
    [self.commandDelegate sendPluginResult:result callbackId:command.callbackId];
}

- (void) sendPluginResultBool: (BOOL)result :(CDVInvokedUrlCommand*)command
{
    CDVPluginResult* pluginResult;
    if(result) {
        pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsInt:1];
    } else {
        pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsInt:0];
    }
    [self.commandDelegate sendPluginResult:pluginResult callbackId:command.callbackId];
}

- (void) handlePluginException: (NSException*) exception :(CDVInvokedUrlCommand*)command
{
    CDVPluginResult* pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_ERROR messageAsString:exception.reason];
    [self.commandDelegate sendPluginResult:pluginResult callbackId:command.callbackId];
}

- (void)jsCallback: (NSString*)jsString
{
    [self.commandDelegate evalJs:jsString];
}

/********************************/
#pragma mark - utility functions
/********************************/

- (BOOL) isMotionAvailable
{
    return [CMMotionActivityManager isActivityAvailable];
}

- (BOOL) isMotionRequestOutcomeAvailable
{
    return [CMPedometer respondsToSelector:@selector(isPedometerEventTrackingAvailable)] && [CMPedometer isPedometerEventTrackingAvailable];
}


- (NSString*) getLocationAuthorizationStatusAsString: (CLAuthorizationStatus)authStatus
{
    NSString* status;
    if(authStatus == kCLAuthorizationStatusDenied || authStatus == kCLAuthorizationStatusRestricted){
        status = @"denied";
    }else if(authStatus == kCLAuthorizationStatusNotDetermined){
        status = @"not_determined";
    }else if(authStatus == kCLAuthorizationStatusAuthorizedAlways){
        status = @"authorized";
    }else if(authStatus == kCLAuthorizationStatusAuthorizedWhenInUse){
        status = @"authorized_when_in_use";
    }
    return status;
}

- (BOOL) isLocationAuthorized
{
    CLAuthorizationStatus authStatus = [CLLocationManager authorizationStatus];
    NSString* status = [self getLocationAuthorizationStatusAsString:authStatus];
    if([status  isEqual: @"authorized"] || [status  isEqual: @"authorized_when_in_use"]) {
        return true;
    } else {
        return false;
    }
}

- (void)locationManager:(CLLocationManager *)manager didChangeAuthorizationStatus:(CLAuthorizationStatus)authStatus {
    NSString* status = [self getLocationAuthorizationStatusAsString:authStatus];
    BOOL statusChanged = false;
    if(self.currentLocationAuthorizationStatus != nil && ![status isEqual: self.currentLocationAuthorizationStatus]){
        statusChanged = true;
    }
    self.currentLocationAuthorizationStatus = status;
    
    if(!statusChanged) return;
    
    
    NSLog(@"%@",[NSString stringWithFormat:@"Location authorization status changed to: %@", status]);
    
    if(self.locationRequestCallbackId != nil){
        CDVPluginResult* pluginResult = [CDVPluginResult resultWithStatus:CDVCommandStatus_OK messageAsString:status];
        [self.commandDelegate sendPluginResult:pluginResult callbackId:self.locationRequestCallbackId];
        self.locationRequestCallbackId = nil;
    }
    
    [self jsCallback:[NSString stringWithFormat:@"cordova.plugins.diagnostic._onLocationStateChange(\"%@\");", status]];
}

- (BOOL) isCameraPresent
{
    BOOL cameraAvailable =
    [UIImagePickerController
     isSourceTypeAvailable:UIImagePickerControllerSourceTypeCamera];
    if(cameraAvailable) {
        NSLog(@"Camera available");
        return true;
    }
    else {
        NSLog(@"Camera unavailable");
        return false;
    }
}

- (BOOL) isCameraAuthorized
{
    AVAuthorizationStatus authStatus = [AVCaptureDevice authorizationStatusForMediaType:AVMediaTypeVideo];
    if(authStatus == AVAuthorizationStatusAuthorized) {
        return true;
    } else {
        return false;
    }
}

- (NSString*) getCameraRollAuthorizationStatus
{
    PHAuthorizationStatus authStatus = [PHPhotoLibrary authorizationStatus];
    return [self getCameraRollAuthorizationStatusAsString:authStatus];
    
}

- (NSString*) getCameraRollAuthorizationStatusAsString: (PHAuthorizationStatus)authStatus
{
    NSString* status;
    if(authStatus == PHAuthorizationStatusDenied || authStatus == PHAuthorizationStatusRestricted){
        status = @"denied";
    }else if(authStatus == PHAuthorizationStatusNotDetermined ){
        status = @"not_determined";
    }else if(authStatus == PHAuthorizationStatusAuthorized){
        status = @"authorized";
    }
    return status;
}

- (BOOL) connectedToWifi  // Don't work on iOS Simulator, only in the device
{
    struct ifaddrs *addresses;
    struct ifaddrs *cursor;
    BOOL wiFiAvailable = NO;
    
    if (getifaddrs(&addresses) != 0) {
        return NO;
    }
    
    cursor = addresses;
    while (cursor != NULL)  {
        if (cursor -> ifa_addr -> sa_family == AF_INET && !(cursor -> ifa_flags & IFF_LOOPBACK)) // Ignore the loopback address
        {
            // Check for WiFi adapter
            if (strcmp(cursor -> ifa_name, "en0") == 0) {
                
                NSLog(@"Wifi ON");
                wiFiAvailable = YES;
                break;
            }
        }
        cursor = cursor -> ifa_next;
    }
    freeifaddrs(addresses);
    return wiFiAvailable;
}

- (NSString*) arrayToJsonString:(NSArray*)inputArray
{
    NSError* error;
    NSData* jsonData = [NSJSONSerialization dataWithJSONObject:inputArray options:NSJSONWritingPrettyPrinted error:&error];
    NSString* jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    return jsonString;
}

- (NSString*) objectToJsonString:(NSDictionary*)inputObject
{
    NSError* error;
    NSData* jsonData = [NSJSONSerialization dataWithJSONObject:inputObject options:NSJSONWritingPrettyPrinted error:&error];
    NSString* jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    return jsonString;
}

#if __IPHONE_OS_VERSION_MAX_ALLOWED < __IPHONE_9_0
- (ABAddressBookRef)addressBook {
    if (!_addressBook) {
        ABAddressBookRef addressBook = ABAddressBookCreateWithOptions(NULL, NULL);
        
        if (addressBook) {
            [self setAddressBook:CFAutorelease(addressBook)];
        }
    }
    
    return _addressBook;
}

- (void)setAddressBook:(ABAddressBookRef)newAddressBook {
    if (_addressBook != newAddressBook) {
        if (_addressBook) {
            CFRelease(_addressBook);
        }
        
        if (newAddressBook) {
            CFRetain(newAddressBook);
        }
        
        _addressBook = newAddressBook;
    }
}

- (void)dealloc {
    if (_addressBook) {
        CFRelease(_addressBook);
        _addressBook = NULL;
    }
}
#endif

- (NSString*)getBluetoothState{
    NSString* state;
    NSString* description;
    
    switch(self.bluetoothManager.state)
    {
            
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
        case CBManagerStateResetting:
#else
        case CBCentralManagerStateResetting:
#endif
            state = @"resetting";
            description =@"The connection with the system service was momentarily lost, update imminent.";
            break;
            
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
        case CBManagerStateUnsupported:
#else
        case CBCentralManagerStateUnsupported:
#endif
            state = @"unsupported";
            description = @"The platform doesn't support Bluetooth Low Energy.";
            break;
            
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
        case CBManagerStateUnauthorized:
#else
        case CBCentralManagerStateUnauthorized:
#endif
            state = @"unauthorized";
            description = @"The app is not authorized to use Bluetooth Low Energy.";
            break;
            
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
        case CBManagerStatePoweredOff:
#else
        case CBCentralManagerStatePoweredOff:
#endif
            state = @"powered_off";
            description = @"Bluetooth is currently powered off.";
            break;
            
#if defined(__IPHONE_10_0) && __IPHONE_OS_VERSION_MAX_ALLOWED >= __IPHONE_10_0
        case CBManagerStatePoweredOn:
#else
        case CBCentralManagerStatePoweredOn:
#endif
            state = @"powered_on";
            description = @"Bluetooth is currently powered on and available to use.";
            break;
        default:
            state = @"unknown";
            description = @"State unknown, update imminent.";
            break;
    }
    NSLog(@"Bluetooth state changed: %@",description);
    
    
    return state;
}

/********************************/
#pragma mark - CBCentralManagerDelegate
/********************************/

- (void) centralManagerDidUpdateState:(CBCentralManager *)central {
    
    NSString* state = [self getBluetoothState];
    NSString* jsString = [NSString stringWithFormat:@"cordova.plugins.diagnostic._onBluetoothStateChange(\"%@\");", state];
    [self jsCallback:jsString];
}

@end
