"use strict";

const download = document.getElementById('download');
const download_btn = document.getElementById('download_btn');
const url = document.getElementById('url');
const vlive_modal_save_btn = document.getElementById('vlive_modal_save_btn');

function link_click(el) {
    const gaSeq = el.dataset.gaSeq;
    url.value = `https://www.vlive.tv/video/${gaSeq}`;
    $('#vlive_modal').modal();
}

// 다운로드
download_btn.addEventListener('click', (event) => {
    event.preventDefault();
    if (download.value.search(/https?:\/\/www\.vlive\.tv\/.+/u) === -1) {
        notify('V LIVE URL을 입력하세요.', 'warning');
        return;
    }
    url.value = download.value;
    $('#vlive_modal').modal();
});

// 다운로드 추가
vlive_modal_save_btn.addEventListener('click', (event) => {
    event.preventDefault();
    const form_data = new URLSearchParams(get_formdata('#modal_form'));
    form_data.append('download[]', url.value);
    fetch(`/${package_name}/ajax/add_download`, {
        method: 'POST',
        cache: 'no-cache',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        },
        body: form_data
    }).then(response => response.json()).then((data) => {
        notify(`${data}개를 큐에 추가하였습니다.`, 'success');
    }).catch(() => {
        notify('실패하였습니다.', 'danger');
    });
    $('#vlive_modal').modal('hide');
});
