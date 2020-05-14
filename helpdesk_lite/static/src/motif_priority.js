function get_priority(){
var data = [];
var id_motif = $('#motif').find(":selected").attr('value')
var url = 'http://localhost:8069/helpdesk/priority?id_motif='+id_motif;
data = $.ajax({
            type: "GET", //rest Type
            dataType: 'jsonp', //mispelled
            url: url,
            async: false,

            success: function (msg) {
                console.log(this.responseText);
            }
        }).responseText;
        console.log(data)

        data = JSON.parse(data);
        console.log(data)
        $('#priority').empty()
        for (i = 0; i < data.length; i++) {
             $('#priority').append("<option value='" + data[i].valeur + "' name='priority'>"
                                        + data[i].valeur +
                               "</option>")
          }
}