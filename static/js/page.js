function lockOption() {
    var selectedValue = getOption();
    selectedValue.text = selectedValue.text + ' (Already Running)';
    selectedValue.disabled = true;
}

function unlockOption(value) {
    var selectedValue = getOption();
    selectedValue.text = value.charAt(0).toUpperCase() + value.slice(1);
    selectedValue.disabled = false;
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
        `<div class="progress" id="#progress-bar-${value}">
            <div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0"
                 aria-valuemax="100" style="width: 100%">
                <span>${value.charAt(0).toUpperCase() + value.slice(1)} is parsing. Please wait<span class="dotdotdot"></span></span>
            </div>
        </div>`
    );
    ajaxRunTask(value);
}

function checkStatus(task_id, value) {
    var intervalID = window.setInterval(function (task_id) {
        $.ajax(
            {
                url: window.location.href + 'task-status/' + task_id,
                type: 'Get',
                data: task_id,
                dataType: 'json',
                success: function (response) {
                    console.log(response);
                    if (response.result != null) {
                        clearInterval(intervalID);
                        removeTaskProgressBar(value);
                        unlockOption(value);
                    }
                }
            }
        );
    }, 2000, task_id);
}


function removeTaskProgressBar(value) {
    var progressbar = document.getElementById('#progress-bar-' + value);
    progressbar.parentNode.removeChild(progressbar);
}

function ajaxRunTask(value) {
    $.ajax(
        {
            url: window.location.href + 'run-task/' + value,
            type: 'Get',
            data: value,
            dataType: 'json',
            success: function (response) {
                checkStatus(response.task_id, value)
            }
        }
    );
}
