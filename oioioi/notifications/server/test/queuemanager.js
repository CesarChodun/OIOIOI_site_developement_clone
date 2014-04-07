var queuemanager = require('../queuemanager');
var CONFIG = require('config');
var rabbit = require('rabbit.js');
var assert = require('assert');

describe('QueueManager', function() {
    var context;
    before(function(done) {
        context = rabbit.createContext(CONFIG.AMQP.Url);
        queuemanager.init(context, done);
    });

    it ('should receive a message for user it is subscribed to', function(done) {
        var testDone = false;
        queuemanager.on('message', function(userName, message) {
            if (!testDone) {
                assert.equal(userName, 'test_user');
                assert.equal(message.message, 'hello');
                assert.ok(queuemanager.acknowledge('test_user', 1));
                done();
                testDone = true;
            }
        });
        queuemanager.subscribe('test_user');
        var push = context.socket('PUSH');
        push.connect('test_user', function() {
            push.write('{"id":1, "message":"hello"}', 'utf8');
        });
    });

    it ('should not acknowledge an unknown message', function() {
       assert.ok(!queuemanager.acknowledge('no_user', 1));
    });


});