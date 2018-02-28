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
    var value = getOption().value;
    lockOption();
    var divToInsert = document.getElementById('#progress-bar-div');
    divToInsert.insertAdjacentHTML(
        'beforeend',
        `<div class="progress" id="progress-bar-${value}">
            <div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0"
                 aria-valuemax="100" style="width: 100%">
                <span>${value.charAt(0).toUpperCase() + value.slice(1)} is parsing. Please wait<span class="dotdotdot"></span></span>
            </div>
        </div>`
    );
}

function checkStatus () {

}