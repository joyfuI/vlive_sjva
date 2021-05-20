"use strict";

const add_btn = document.getElementById('add_btn');
const list_div = document.getElementById('list_div');
const modal_form = document.getElementById('modal_form');
const db_id = document.getElementById('db_id');
const url = document.getElementById('url');
const save_path = document.getElementById('save_path');
const filename = document.getElementById('filename');
const is_live = document.getElementById('is_live');
const schedule_modal_save_btn = document.getElementById('schedule_modal_save_btn');
const confirm_title = document.getElementById('confirm_title');
const confirm_body = document.getElementById('confirm_body');

let current_data;

is_live.disabled = true;

// 리스트 로딩
fetch(`/${package_name}/ajax/list_scheduler`, {
    method: 'POST',
    cache: 'no-cache',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
}).then(response => response.json()).then(make_list);

// 스케줄 추가
add_btn.addEventListener('click', (event) => {
    event.preventDefault();
    db_id.value = '';
    url.disabled = false;
    modal_form.reset();
    $('#is_live').bootstrapToggle('on');
    $('#schedule_modal').modal();
});

list_div.addEventListener('click', (event) => {
    event.preventDefault();
    const target = event.target;
    if (target.tagName !== 'BUTTON') {
        return;
    }
    const index = target.dataset.id;
    if (target.classList.contains('vlive-edit')) {
        // 스케줄 수정
        db_id.value = index;
        url.value = current_data[index].url;
        url.disabled = true;
        save_path.value = current_data[index].save_path;
        filename.value = current_data[index].filename;
        $('#is_live').bootstrapToggle((current_data[index].is_live) ? 'on' : 'off');
        $('#schedule_modal').modal();
    } else if (target.classList.contains('vlive-del')) {
        // 스케줄 삭제
        confirm_title.textContent = '스케줄 삭제';
        confirm_body.textContent = '해당 스케줄을 삭제하시겠습니까?';
        $('#confirm_button').off('click').click(index, del_scheduler);
        $('#confirm_modal').modal();
    }
});

// 스케줄 저장
schedule_modal_save_btn.addEventListener('click', (event) => {
    event.preventDefault();
    $('#schedule_modal').modal('hide');
    if (url.value.search(/https?:\/\/www\.vlive\.tv\/channel\/\w+/u) === -1) {
        notify('V LIVE 채널 URL을 입력하세요.', 'warning');
        return;
    }
    fetch(`/${package_name}/ajax/add_scheduler`, {
        method: 'POST',
        cache: 'no-cache',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        },
        body: get_formdata('#modal_form')
    }).then(response => response.json()).then((data) => {
        if (data === null) {
            notify('V LIVE 채널을 분석하지 못했습니다.', 'warning');
            return;
        }
        make_list(data);
        notify('스케줄을 저장하였습니다.', 'success');
    }).catch(() => {
        notify('실패하였습니다.', 'danger');
    });
});

function make_list(data) {
    current_data = {};
    let str = '';
    for (const item of data) {
        current_data[item.id] = item;
        str += make_item(item);
    }
    list_div.innerHTML = str;
}

function make_item(data) {
    let str = m_row_start();
    let tmp = `<strong><a href="${data.url}" target="_blank">${data.title}</a></strong>`;
    str += m_col(3, tmp);

    tmp = m_row_start(0);
    tmp += m_col2(3, '저장 경로', 'right');
    tmp += m_col2(9, data.path);
    tmp += m_row_end();
    tmp += m_row_start(0);
    tmp += m_col2(3, 'LIVE만 다운로드', 'right');
    tmp += m_col2(9, (data.is_live) ? 'O' : 'X');
    tmp += m_row_end();
    str += m_col(5, tmp);

    tmp = `동영상 개수: ${data.count}<br>`;
    tmp += `마지막 실행: ${data.last_time}<br><br>`;
    let tmp2 = `<button class="btn btn-sm btn-outline-success vlive-edit" data-id="${data.id}">스케줄 수정</button>`;
    tmp2 += `<button class="btn btn-sm btn-outline-success vlive-del" data-id="${data.id}">스케줄 삭제</button>`;
    tmp += m_button_group(tmp2);
    str += m_col(4, tmp);

    str += m_row_end();
    str += m_hr(0);
    return str;
}

// 스케줄 삭제
function del_scheduler(event) {
    event.preventDefault();
    fetch(`/${package_name}/ajax/del_scheduler`, {
        method: 'POST',
        cache: 'no-cache',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        },
        body: new URLSearchParams({
            id: event.data
        })
    }).then(response => response.json()).then((data) => {
        make_list(data);
        notify('삭제하였습니다.', 'success');
    }).catch(() => {
        notify('실패하였습니다.', 'danger');
    });
}
