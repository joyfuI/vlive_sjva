"use strict";

const url = document.getElementById('url');
const is_live = document.getElementById('is_live');
const vlive_modal_save_btn = document.getElementById('vlive_modal_save_btn');

function link_click(el) {
    const gaSeq = el.dataset.gaSeq;
    url.value = `https://www.vlive.tv/video/${gaSeq}`;
    $('#vlive_modal').modal();
}

is_live.disabled = true;

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
