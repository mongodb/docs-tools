/**
 * Copyright 2014 MongoDB, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
**/

$(document).ready(function(){
    $(".edit").on('click',edit);
    $(".approve").on('click',approve);
    $(".unapprove").on('click',unapprove);
    $(".language").on('click',language);
    $("#show-unapproved-button").on('click',toggle_approved);

    $(".target").each(check_approval);
    $(".target").each(check_editor);
    $('textarea').autosize();

    $('#upload-btn').on('click',upload);
    $('#download-all-btn').on('click', download_all);
    $('#download-approved-btn').on('click', download_approved);

})


function download_all(){
    if($('#download-file-path').val() == "ALL"){
        var url = 'download-all/'+$('#target_language_download').val();
    }
    else{
        var url = 'download-all/'+$('#target_language_download').val()+'/'+$('#download-file-path').val();
    }
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data, textStatus, jqXHR){
            if(typeof data.error === 'undefined'){
                console.log("SUCCESS");
                $("body").append("<iframe src='" + url + "' style='display: none;' ></iframe>");
            }
            else{
                console.log('ERRORS: ' + data.error);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log('ERRORS: ' + textStatus);
        }
    });

}

function download_approved(){
    if($('#download-file-path').val() == "ALL"){
        var url = 'download-approved/'+$('#target_language_download').val();
    }
    else{
        var url = 'download-approved/'+$('#target_language_download').val()+'/'+$('#download-file-path').val();
    }
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data, textStatus, jqXHR){
            if(typeof data.error === 'undefined'){
                console.log("SUCCESS");
                $("body").append("<iframe src='" + url + "' style='display: none;' ></iframe>");
            }
            else{
                console.log('ERRORS: ' + data.error);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log('ERRORS: ' + textStatus);
        }
    });

}

function upload(){
    
    var filelist =  document.getElementById("file").files || [];
    var data = new FormData();
    data.append('file_name', filelist[0].webkitRelativePath);
    data.append('file', filelist[0]);
    data.append('username', $('#username').val());
    data.append('status', $('#status').val());
    data.append('source_language', $('#source_language').val());
    data.append('target_language', $('#target_language').val());
    $.ajax({
        url: '/upload',
        type: 'POST',
        data: data,
        cache: false,
        dataType: 'json',
        processData: false, // Don't process the files
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        success: function(data, textStatus, jqXHR){
            if(typeof data.error === 'undefined'){
                console.log("SUCCESS");
            }
            else{
                console.log('ERRORS: ' + data.error);
            }
        },
        error: function(jqXHR, textStatus, errorThrown){
            console.log('ERRORS: ' + textStatus);
        }
    });

}

function toggle_approved(){
    var newtext = ($(this).html() == "Show All" ? "Only Show Unapproved" : "Show All");
    $(this).html(newtext);
    $('tr').each(function(){
        if($(this).children(".target").data("sentence").status == "approved"){
            $(this).toggle();
        }
    });
}

function check_approval(){
    var approvers= $(this).data('sentence').approvers;
    for(var i=0; i< approvers.length; i++){
        if(approvers[i].$oid == $('#navigation').data('userid')){
            approve_html($(this).children('.approve'));
        }
    }
}

function check_editor(){
    if($('#navigation').data('userid') == $(this).data('sentence').userID.$oid){
        edit_html($(this).children('.edit'));
    }
}

function edit(e){
    edit_html($(this));
}

function edit_html(e){
    e.parent().children(".approve").attr("disabled",true);
    e.parent().children(".edit").html("Save");
    e.parent().children(".target_sentence").attr("readOnly",false);
    e.parent().children(".target_sentence").css("backgroundColor", "#FFFFFF");
    e.parent().children(".edit").off('click').on('click',save);

}

function toggle_message(msg, color){

    $('#error-message').val(msg);
    $('#error-message').css("color",color);
    $("#error-message").show()
    setTimeout(function() {
            $("#error-message").hide()
    }, 3000);

}

function lock_error(json_data){
    window.location.replace('/edit/'+json_data.username+'/'+json_data.target_language+'/'+json_data.file_path+'/423');
}

function save(){
    var new_content={"editor": $("#username").val(), "new_target_sentence": $(this).parent().children(".target_sentence").val()};
    var j={"old": $(this).parent().data("sentence"), "new": new_content};
    $.ajax({
          type: "POST",
          contentType: "application/json; charset=utf-8",
          url: "/add",
          data: JSON.stringify(j),
          dataType: "json",
          success: function(data, textStatus, jqxhr)
                   {
                        toggle_message(data.msg, "green");
                   },
          error: function(data, textStatus, jqxhr)
                   {
                        toggle_message("Error: "+data.responseJSON.msg, "red");
                   }
    });
}

function approve(){
    approve_html($(this));
    var $this=$(this);
    var s=$(this).parent().data("sentence");
    var new_content={"approver": $("#username").val()}
    var j={"old": s, "new": new_content};
    $.ajax({
          type: "POST",
          contentType: "application/json; charset=utf-8",
          url: "/approve",
          data: JSON.stringify(j),
          dataType: "json",
          success: function(data, textStatus, jqxhr)
                   {
                        toggle_message(data.msg, "green");
                        var new_approval_num=parseInt($this.parent().children(".approval_num").val())+1;
                        $this.parent().children(".approval_num").val(new_approval_num);
                   },
          error: function(data, textStatus, jqxhr)
                   {
                        if(data.status == 423){
                            lock_error(data.responseJSON);
                        }
                        else{
                            toggle_message("Error: "+data.responseJSON.msg, "red");
                            unapprove_html($this);
                        }
                   }
    });
}

function approve_html(e){
    e.parent().children(".edit").attr("disabled",true);
    e.parent().children(".approve").html("Unapprove");
    e.parent().children(".approve").off('click').on('click', unapprove);
    e.parent().children(".approve").addClass('unapprove').removeClass('approve');

}
function unapprove(){
    unapprove_html($(this))
    var $this=$(this)
    var s=$(this).parent().data("sentence");
    var new_content={"unapprover": $("#username").val()}
    var j={"old": s, "new": new_content};
    $.ajax({
          type: "POST",
          contentType: "application/json; charset=utf-8",
          url: "/unapprove",
          data: JSON.stringify(j),
          dataType: "json",
          success: function(data, textStatus, jqxhr)
                   {
                        toggle_message(data.msg, "green");
                        var new_approval_num=parseInt($this.parent().children(".approval_num").val())-1;
                        $this.parent().children(".approval_num").val(new_approval_num);
                   },
          error: function(data, textStatus, jqxhr)
                   {
                        toggle_message("Error: "+data.responseJSON.msg, "red");
                        approve_html($this);
                   }
    });
}

function unapprove_html(e){
    e.parent().children(".edit").attr("disabled",false);
    e.parent().children(".unapprove").html("Approve");
    e.parent().children(".edit").off('click').on('click', edit);
    e.parent().children(".unapprove").off('click').on('click', approve);
    e.parent().children(".unapprove").addClass('approve').removeClass('unapprove');

}

function language(){
    window.location.href = 'edit/'+$('#username').val()+'/'+$(this).html();
}
