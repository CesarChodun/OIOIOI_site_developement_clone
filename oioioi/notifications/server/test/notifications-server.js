var CONFIG = require('config');
var assert = require('assert');
var auth = require('../auth');
var sinon = require('sinon');
var request = require('request');
var queuemanager = require('../queuemanager');
var nserver = require('../notifications-server');

describe("Server", function() {

    before(function (done) {
        var getter = sinon.stub(request, 'get');
        getter.withArgs(sinon.match.any,
            sinon.match({headers:{Cookie:'sessionid=12345'}}))
            .yields(null, {statusCode: 200}, '{"status": "UNAUTHORIZED"}');
        getter.withArgs(sinon.match.any,
            sinon.match({headers:{Cookie:'sessionid=TEST_USER_SID'}}))
            .yields(null, {statusCode: 200}, '{"status": "OK", "user": "test_user"}');
        queuemanager.init(null, done);
    });

    after(function() {
        request.get.restore();
    });

    it ("should fail an authenticate request", function(done) {
        var socket = {};
        socket.on = sinon.stub();
        socket.on.withArgs('authenticate')
            .yields('{"session_id": "12345"}');

        socket.emit = sinon.spy();
        var failed =
            socket.emit.withArgs("authenticate", sinon.match({status: "ERR_AUTH_FAILED"}));
        nserver.onSocketConnected(socket);
        assert.ok(failed.calledOnce);
        done();
    });

    it ("should succeed with an authenticate request", function(done) {
        var socket = {};
        socket.on = sinon.stub();
        socket.on.withArgs('authenticate')
            .yields('{"session_id": "TEST_USER_SID"}');

        socket.emit = function(key, data) {
            assert.equal(key, 'authenticate');
            assert.equal(data.status, 'OK');
            auth.logout(socket);
            done();
        };
        nserver.onSocketConnected(socket);
    });

    it ("should transmit a message to all 5 sockets of test_user", function(done) {
        var sStub = sinon.stub();
        var numCalled = 0;
        var numMessages = 0;
        function sendMsg() {
            nserver.onMessageReceived('test_user', {id:1, message: 'test_message'});

        }
        var sEmit = function(socket) {
            return function(key, data) {
                if (data.status === 'OK') {
                    numCalled++;
                }
                else //message arrived
                {
                    numMessages++;
                    assert.equal(data.message, 'test_message');
                    if (numMessages === 5) {
                        done();
                    }
                    auth.logout(socket);
                }
                if (numCalled === 5) {
                    numCalled = 0;
                    sendMsg();
                }
            }
        };
        sStub.withArgs('authenticate')
            .yields('{"session_id": "TEST_USER_SID"}');
        var sockets = [{}, {}, {}, {}, {}];
        for (var s in sockets) {
            sockets[s].on = sStub;
            sockets[s].emit = sEmit(sockets[s]);
            nserver.onSocketConnected(sockets[s]);
        }
    });

});