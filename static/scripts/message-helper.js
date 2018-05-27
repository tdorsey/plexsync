var enumify = require('enumify');
var $ = require('jquery');

class MessageType extends enumify.Enum {}

var messageTypeSettings = {
  Primary: {
         value: "primary"
    },
  Secondary: {
        value: "secondary"
    },
  Light: {
        value: "light"
    },
  Dark: {
        value: "dark"
    },
  Success: {
        value: "success"
    },
  Warning: {
        value: "warning"
    },
  Info: {
        value: "info"
    },
  Danger: {
        value: "danger"
    }
};

MessageType.initEnum(messageTypeSettings);

function InvalidOptionsException (message) {
   this.message = message;
   this.name = 'InvalidOptionsException';
}

function validateOptions(options) {
    if (typeof (options) !== "object") {
        throw InvalidOptionsException("Please specify valid message options");
    }
}

function showAll() {
    toggleAll(true);
}

function hideAll() {
    toggleAll(false);
}

function toggleAll(isVisible) {
    for (const t of MessageType.enumValues) {

        elementID =  `alert-${t.value}`;
        messageDiv = $(`.${elementID}`);
        messageDiv.toggle(isVisible);

    }

}
function showMessage(message, options) {
    if (options) {
        validateOptions(options);
    }

    elementID =  `alert-${options.messageType.value}`;
    messageDiv = $(`.${elementID}`);
    messageDiv.toggle(true);
    messageDiv.append(message);

}

var message = {

    show : showAll,
    hide : hideAll
};

//dynamically assign each member of the enum to the export object
for (const t of MessageType.enumValues) {
    val = t.value;
    fn = function (message, options) {
            if (typeof(options) === "undefined") {
                options = {};
            }
            options.messageType = t;
            showMessage(message, options);
    };
    message[t.value] = fn;
}

module.exports = message;
