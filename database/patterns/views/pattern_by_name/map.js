function(doc) {
    if(doc.type=="pattern"){
        emit([doc.pattern, doc.pass], [doc.required_pre, doc.required_post]);
    }
}