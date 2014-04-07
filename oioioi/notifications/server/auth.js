var request = require("request");
var queuemanager = require('./queuemanager');

var CONFIG = require('config').OIOIOI;
// maps sockets to user names
var sockets = {};
// maps users to socket collections
var users = {};

var sessionid_cache = {};

function login(socket, sessionId, onCompleted) {
    auth(sessionId, function(userName) {
        if (!userName) {
            onCompleted(null);
            return;
        }
        sockets[socket.dict_id] = userName;
        if (!users[userName]) {
            users[userName] = {};
            queuemanager.subscribe(userName);
        }
        users[userName][socket.dict_id] = socket;
        onCompleted(userName);
    });

}

function auth(sessionId, onCompleted) {
    if (sessionid_cache[sessionId]) {
        if (Date.now() < sessionid_cache[sessionId].expires) {
            console.log('User ' + sessionid_cache[sessionId].user + ' logged in from cache');
            onCompleted(sessionid_cache[sessionId].user);
            return;
        }
    }

    request.get(
        CONFIG.AuthUrl,
        { headers: {'Cookie' : 'sessionid=' + sessionId } },
        function (error, response, body) {

            if (!error && response.statusCode === 200) {
                body = JSON.parse(body);
                if (body.status !== 'OK') {
                    onCompleted(null);
                }
                else {
                    console.log('Authorized user: ' + body.user);
                    sessionid_cache[sessionId] = {
                        user: body.user,
                        expires: Date.now() +
                            CONFIG.AuthCacheExpirationSeconds * 1000
                    };
                    onCompleted(body.user);
                }
            }
            else {
                if (error) {
                    console.log('Unable to authorize user!');
                    console.log(error);
                }
                onCompleted(null);
            }
        }
    );
}

function resolveUserName(socket) {
    return sockets[socket.dict_id];
}

function getClientsForUser(userName) {
    return users[userName];
}

function logout(socket) {
    var userName = sockets[socket.dict_id];
    if (users[userName]) {
        delete users[userName][socket.dict_id];
        if (Object.keys(users[userName]).length === 0) {
            delete users[userName];
            queuemanager.unsubscribe(userName);
        }
    }
    // console.log("Logging out " + socket.dict_id);
    delete sockets[socket.dict_id];
}

exports.login = login;
exports.logout = logout;
exports.resolveUserName = resolveUserName;
exports.getClientsForUser = getClientsForUser;
