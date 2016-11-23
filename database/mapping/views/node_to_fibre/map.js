function(doc){
    if(doc.type=="PANEL_FIBRE_MAPPING"){
        emit([doc.first_valid, doc.version], doc);
    }
}
