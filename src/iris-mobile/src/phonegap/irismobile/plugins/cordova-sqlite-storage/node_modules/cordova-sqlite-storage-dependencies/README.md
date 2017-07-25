# Cordova sqlite storage dependencies

**AUTHOR:** Christopher J. Brody

**LICENSE:** [Unlicense (unlicense.org)](http://unlicense.org/) (public domain)

Contains source and object code built from:
- SQLite3 from [sqlite.org](http://sqlite.org/) (public domain)
- [liteglue / Android-sqlite-native-driver](https://github.com/liteglue/Android-sqlite-native-driver) (Unlicense, public domain)
- [liteglue / Android-sqlite-connector](https://github.com/liteglue/Android-sqlite-connector) (Unlicense, public domain)

This project provides the following dependencies needed to build [litehelpers / Cordova-sqlite-storage](https://github.com/litehelpers/Cordova-sqlite-storage):
- `sqlite3.h`, `sqlite3.c` - SQLite `3.15.2` amalgamation needed to build iOS and Windows versions
- `libs` - [liteglue / Android-sqlite-connector](https://github.com/liteglue/Android-sqlite-connector) JAR and [liteglue / Android-sqlite-native-driver](https://github.com/liteglue/Android-sqlite-native-driver) NDK libraries built with SQLite `3.15.2` amalgamation, with the following flags:
 - `-DSQLITE_THREADSAFE=1`
 - `-DSQLITE_DEFAULT_MEMSTATUS=0`
 - `-DSQLITE_OMIT_DECLTYPE`
 - `-DSQLITE_OMIT_DEPRECATED`
 - `-DSQLITE_OMIT_PROGRESS_CALLBACK`
 - `-DSQLITE_OMIT_SHARED_CACHE`
 - `-DSQLITE_TEMP_STORE=2`
 - `-DSQLITE_OMIT_LOAD_EXTENSION`
 - `-DSQLITE_ENABLE_FTS3`
 - `-DSQLITE_ENABLE_FTS3_PARENTHESIS`
 - `-DSQLITE_ENABLE_FTS4`
 - `-DSQLITE_ENABLE_RTREE`
 - `-DSQLITE_DEFAULT_PAGE_SIZE=1024`
 - `-DSQLITE_DEFAULT_CACHE_SIZE=2000`
