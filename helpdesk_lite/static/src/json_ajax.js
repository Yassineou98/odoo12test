function get_motif(){
var data = [];
var id_type = $('#type').find(":selected").attr('value')
var url = 'http://localhost:8069/helpdesk/motifs?id_type='+id_type;
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
        $('#motif').empty()
        $('#motif').append("<option>select motif</option>")
        for (i = 0; i < data.length; i++) {
            $('#motif').append("<option  value='" + data[i].id + "' name='motif'>"
                                        + data[i].valeur +
                               "</option>")
        }
}