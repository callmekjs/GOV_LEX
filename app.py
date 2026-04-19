"""
GovLex-Ops 검색 UI.
실행: streamlit run app.py
"""
import streamlit as st
import json
from pathlib import Path
from govlexops.search.indexer import search, load_docs
from govlexops.core.storage import count_documents

# ── 페이지 설정 ──
st.set_page_config(
    page_title="GovLex-Ops",
    page_icon="⚖️",
    layout="wide",
)

# ── 헤더 ──
st.title("⚖️ GovLex-Ops")
st.caption("한국·미국 법·입법 공개 데이터 검색 파이프라인")

# ── 상단 통계 ──
stats = count_documents()
col1, col2, col3 = st.columns(3)
col1.metric("🇰🇷 한국 문서", f"{stats['KR']}건")
col2.metric("🇺🇸 미국 문서", f"{stats['US']}건")
col3.metric("📦 전체", f"{stats['total']}건")

st.divider()

# ── 검색 영역 ──
st.subheader("🔍 문서 검색")

col_query, col_filter = st.columns([3, 1])

with col_query:
    query = st.text_input(
        "검색어",
        placeholder="예: 인공지능, AI regulation, 데이터...",
        label_visibility="collapsed",
    )

with col_filter:
    jurisdiction = st.selectbox(
        "국가",
        ["전체", "KR", "US"],
        label_visibility="collapsed",
    )

# ── 예시 검색어 버튼 ──
st.write("예시:")
ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)
if ex_col1.button("인공지능"):
    query = "인공지능"
if ex_col2.button("AI regulation"):
    query = "AI regulation"
if ex_col3.button("데이터"):
    query = "데이터"
if ex_col4.button("privacy"):
    query = "privacy"

# ── 검색 실행 ──
if query:
    results = search(query=query, top_k=10, jurisdiction=jurisdiction)

    if results:
        st.success(f"**{len(results)}건** 검색됨")
        st.divider()

        for i, doc in enumerate(results, 1):
            # 국가 태그 색상
            if doc.get("jurisdiction") == "KR":
                tag = "🇰🇷 한국"
                tag_color = "🔵"
            else:
                tag = "🇺🇸 미국"
                tag_color = "🔴"

            # 문서 카드
            with st.container():
                col_num, col_content = st.columns([0.5, 9.5])

                with col_num:
                    st.write(f"**{i}**")

                with col_content:
                    st.markdown(f"### {doc.get('title', '제목 없음')}")

                    info_col1, info_col2, info_col3 = st.columns(3)
                    info_col1.write(f"{tag_color} **{tag}**")
                    info_col2.write(f"📅 {doc.get('issued_date', '-')}")
                    info_col3.write(f"📄 {doc.get('source_type', '-')}")

                    source_url = doc.get("source_url", "")
                    if source_url:
                        st.markdown(f"🔗 [원문 보기]({source_url})")

                    # 메타데이터 접기
                    metadata = doc.get("metadata", {})
                    if metadata:
                        with st.expander("상세 정보"):
                            st.json(metadata)

            st.divider()

    else:
        st.warning(f"**'{query}'** 검색 결과가 없습니다. 다른 검색어를 시도해보세요.")

else:
    # 검색어 없을 때 최근 문서 5개 보여주기
    st.write("#### 최근 수집 문서")
    docs = load_docs()
    if docs:
        recent = docs[-5:][::-1]
        for doc in recent:
            flag = "🇰🇷" if doc.get("jurisdiction") == "KR" else "🇺🇸"
            st.write(
                f"{flag} **{doc.get('title', '?')}** "
                f"— {doc.get('issued_date', '-')}"
            )
    else:
        st.info("데이터가 없습니다. 파이프라인을 먼저 실행해주세요.")
        st.code("python -m govlexops.etl.pipeline")