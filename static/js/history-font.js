'use strict';
var sizeRule = null;

var sheets = document.styleSheets;
for (let sheet of sheets) {
    if (sheet.ownerNode.id === "history-css") {
        for (let rule of sheet.cssRules) {
            for (let prop of rule.style) {
                if (prop === "font-size") {
                    sizeRule = rule;
                }
            }
        }
    }
}

function increaseSize(size) {
    setFontSize(getFontSize() + size);
}

function getFontSize() {
    var currentSizeStr = sizeRule.style["font-size"];
    var currentSize = parseFloat(currentSizeStr.substr(0, currentSizeStr.length-2));
    return currentSize;
}

function setFontSize(newSize) {
    localStorage.setItem('fontsize', newSize);
    sizeRule.style["font-size"] = newSize+"em";
}

function fontSizeSetup() {
    var storageFont = localStorage.getItem('fontsize');

    if (storageFont === null) {
       localStorage.setItem('fontsize', 0.5);
       storageFont = "0.5";
    }

    setFontSize(storageFont);
}

document.addEventListener('DOMContentLoaded', fontSizeSetup);