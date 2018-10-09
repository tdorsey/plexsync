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

function isMessageType(maybeMessageType) {
    return maybeMessageType instanceof MessageType; 
}

function _convertToMessageType(messageValue) {
    value = messageValue;
    //convert it to a MessageType if it isn't already
    if (typeof value === "string") {
        //capitalize it so we can check if it's an enum value
        capitalizedValue = value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();

        //Get the enum from the capitalized value and make sure it's valid
         m = MessageType.enumValueOf(capitalizedValue);
    }

    else {
        m = messageType
    }

    if (isMessageType(m)) {
        return m;
    }
    else {
        throw InvalidOptionsException(`${value} is not a valid MessageType`);
    }

}

function validateOptions(options) {
    if (typeof (options) !== "object") {
        throw InvalidOptionsException("Please specify valid message options object");
    }

    if (options.messageType && !isMessageType(options.messageType)) {
        options.messageType = _convertToMessageType(options.messageType);
    }

    if (options.removeOthers && !typeof(options.removeOthers !== "boolean")) {
        throw InvalidOptionsException(`${options.removeOthers} is not a boolean`);
    }
}

function showAll() {
    toggleAll(true);
}

function hideAll() {
    toggleAll(false);
}

function clearAll() {
    for (const t of MessageType.enumValues) {
            elementID =  `alert-${t.value}`;
            messageDiv = $(`.${elementID}`);
            messageDiv.text("")
    }
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

    if (options.removeOthers) {
        clearAll();
        hideAll();
    }

    elementID =  `alert-${options.messageType.value}`;
    messageDiv = $(`.${elementID}`);
    messageDiv.toggle(true);
    messageDiv.text(message);

}

var message = {

    show  : showAll,
    hide  : hideAll,
    clear : clearAll,
    showMessage : showMessage
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
