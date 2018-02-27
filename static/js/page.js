function lockOption() {
    var selectedValue = getOption();
    selectedValue.text= selectedValue.text +' (Already Running)';
    selectedValue.disabled = true;
}

function getOption() {
    var selectBox = document.getElementById("inputGroupSelect");
    var selectedValue = selectBox.options[selectBox.selectedIndex];
    return selectedValue;
}

function sendStartTaskData() {
    lockOption();

}

function checkStatus () {

}