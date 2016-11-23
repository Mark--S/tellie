function(doc){
    if(doc.type=="TELLIE_PATCH_MAPPING"){
        emit([doc.first_valid, doc.timestamp], [1]);
    }
}
