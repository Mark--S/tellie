function(doc) {
    if(doc.type=="PATTERN"){
        emit([doc.pattern, doc.pass], [doc.required_pre, doc.required_post]);
    }
}
