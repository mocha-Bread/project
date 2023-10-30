#  사용자 취향 맞춤형 향수 추천 시스템 및 분사

<h1>설명</h1>

- 웹에서 사용자로부터 질문을 하고 답변을 토대로 openai의 davinci 모델을 사용해서 취향에 맞는 향 추천 구현 <BR>

- DB에 있는 여러 향 중에서 추천된 향에 해당하는 향수 제품 및 향수 사진을 DB로부터 가져와서 웹상에 출력


<H3>테스트.py</H3>

> 파일내에 openai api key 입력필요 <br>
> mysql 사용시 만들어둔 sql문 실행 필요

<H3>주의사항</H3>

> s3스토리지 사용으로 이미지가 손실될 가능성이 높아 sql문에 s3 주소를 로컬주소 혹은 s3에 직접 올려서 객체주소로 변경해야함
> ex) https://s3.ap-northeast-2.amazonaws.com/perfume.projact/perfume_projact/%ED%96%A5%EC%88%9838.jpg 이런주소를 변경해야할수도 있음
