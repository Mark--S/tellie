function(doc){
    if(doc.type=="TELLIE_RUN_PLAN"){
        emit(doc.name, doc);
    }
}
