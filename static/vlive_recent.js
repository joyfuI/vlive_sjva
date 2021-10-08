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

const post_ajax = (url, data) => fetch(`/${package_name}/ajax/${url}`, {
    method: 'POST',
    cache: 'no-cache',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    },
    body: new URLSearchParams(data)
}).then(response => response.json()).then((ret) => {
    if (ret.msg) {
        notify(ret.msg, ret.ret);
    }
    return ret;
});

// 다운로드
download_btn.addEventListener('click', (e) => {
    e.preventDefault();
    if (download.value.search(/https?:\/\/www\.vlive\.tv\/.+/u) === -1) {
        notify('V LIVE URL을 입력하세요.', 'warning');
        return;
    }
    url.value = download.value;
    $('#vlive_modal').modal();
});

// 다운로드 추가
vlive_modal_save_btn.addEventListener('click', (e) => {
    e.preventDefault();
    const form_data = new URLSearchParams(get_formdata('#modal_form'));
    form_data.append('download[]', url.value);
    post_ajax('/add_download', form_data);
});
