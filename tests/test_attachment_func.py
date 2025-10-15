from utils.attachment import decode_attachments, summarize_attachment_meta

attachments = [
    {
        "name": "hello.txt",
        "url": "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
    },
    {
        "name": "data.csv",
        "url": "data:text/csv;base64,Y29sMSxjb2wyLGNvbDMKMSwyLDMKNiw3LDgK"
    }
]


saved = decode_attachments(attachments)
print(saved)

summary = summarize_attachment_meta(saved)
print(summary)
