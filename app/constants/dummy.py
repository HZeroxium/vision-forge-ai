# app/constants/dummy.py

from app.models.schemas import (
    CreateScriptResponse,
    CreateImagePromptsResponse,
    CreateImageResponse,
    CreateAudioResponse,
)

DUMMY_SCRIPT_RESPONSE = CreateScriptResponse(
    content="Quá trình sinh trưởng của thực vật là một chủ đề thú vị và đầy màu sắc trong thế giới tự nhiên. Khi nhìn ra ngoài, chúng ta thường thấy cây cối vươn mình, nở hoa và ra trái. Nhưng điều gì thực sự diễn ra bên trong những sinh vật này? Hãy cùng khám phá.\n\nSinh trưởng của thực vật bắt đầu từ hạt giống. Một hạt giống chứa tất cả các thông tin di truyền cần thiết để phát triển thành một cây hoàn chỉnh. Khi hạt giống gặp môi trường thuận lợi, như độ ẩm và nhiệt độ thích hợp, nó bắt đầu nảy mầm. Quá trình này giống như một phép màu, khi hạt giống hấp thụ nước và dinh dưỡng từ đất, kích thích sự phát triển của rễ và mầm cây.\n\nRễ cây là bộ phận quan trọng đầu tiên phát triển. Chúng không chỉ giúp cây bám chặt vào mặt đất mà còn hấp thụ nước và khoáng chất cần thiết cho sự phát triển. Khi rễ mạnh mẽ, mầm cây bắt đầu vươn lên, tìm kiếm ánh sáng mặt trời. Ánh sáng là nguồn năng lượng chính cho thực vật, giúp chúng thực hiện quá trình quang hợp.\n\nQuang hợp là một quá trình kỳ diệu, mà qua đó cây cối chuyển đổi ánh sáng mặt trời thành năng lượng. Trong quá trình này, cây hấp thụ carbon dioxide từ không khí và nước từ đất, sau đó sản xuất ra glucose và oxy. Glucose là nguồn năng lượng mà cây sử dụng để phát triển, trong khi oxy được thải ra, cung cấp cho chúng ta không khí trong lành.\n\nKhi cây trưởng thành, nó sẽ trải qua nhiều giai đoạn sinh trưởng khác nhau. Cây sẽ phát triển thêm thân, lá và hoa. Mỗi bộ phận này đóng một vai trò quan trọng trong quá trình sinh trưởng và sinh sản. Thân cây không chỉ hỗ trợ cấu trúc mà còn vận chuyển nước và chất dinh dưỡng giữa các bộ phận. Lá cây, với bề mặt rộng và xanh tươi, là nơi diễn ra quang hợp, cung cấp năng lượng cho toàn bộ cây.\n\nKhi đến giai đoạn trưởng thành, cây sẽ bắt đầu ra hoa. Hoa không chỉ đẹp mắt mà còn là phần quan trọng trong quá trình sinh sản. Chúng thu hút côn trùng thụ phấn, giúp cho quá trình thụ tinh diễn ra. Sau khi thụ tinh, hoa sẽ phát triển thành trái, bên trong chứa hạt giống cho thế hệ cây kế tiếp.\n\nQuá trình sinh trưởng của thực vật không chỉ đơn thuần là sự phát triển của cây mà còn là một chu trình liên kết với môi trường xung quanh. Thực vật tương tác với đất, nước, ánh sáng và khí hậu, tạo thành một hệ sinh thái phong phú. Sự sinh trưởng của thực vật đóng vai trò quan trọng trong việc duy trì sự cân bằng sinh thái, cung cấp thực phẩm, nơi sống và oxy cho các sinh vật khác.\n\nTóm lại, quá trình sinh trưởng của thực vật bắt đầu từ hạt giống và trải qua nhiều giai đoạn khác nhau, từ nảy mầm, phát triển rễ và mầm, đến trưởng thành và ra hoa. Mỗi giai đoạn đều có những chức năng và vai trò quan trọng, không chỉ cho bản thân cây mà còn cho toàn bộ hệ sinh thái. Qua đó, chúng ta thấy được vẻ đẹp và sự kỳ diệu của thế giới thực vật xung quanh mình."
)
DUMMY_IMAGE_PROMPTS_RESPONSE = CreateImagePromptsResponse(
    prompts=[
        {
            "prompt": "**Seed Germination**: A close-up view of a seed nestled in dark, moist soil, with delicate white roots beginning to sprout downward and a tiny green shoot breaking through the soil surface. The scene is illuminated by soft sunlight filtering through leaves above, highlighting the textures of the soil and the seed."
        },
        {
            "prompt": "**Root System Development**: A cross-section of soil revealing a young plant with an intricate network of roots spreading out in different directions. The roots are shown absorbing water and nutrients from the surrounding soil, with tiny soil particles clinging to them. The background features layers of soil with varying textures to emphasize the underground ecosystem."
        },
        {
            "prompt": "**Photosynthesis Process**: A vibrant, wide shot of a mature plant with large green leaves absorbing sunlight, showing the sunlight streaming down. The leaves are dotted with small openings (stomata) that are actively taking in carbon dioxide from the air, while roots are absorbing water from the soil below. Bubbles of oxygen are depicted emerging from the leaves, symbolizing the oxygen produced during photosynthesis."
        },
        {
            "prompt": "**Plant Growth Stages**: A series of four panels showing the different stages of plant growth: the first panel with a seed, the second showing a sprouted seedling, the third displaying a small plant with leaves, and the final panel featuring a fully mature plant with flowers. Each panel should be connected by a continuous line or gradient background to represent the progression of growth."
        },
        {
            "prompt": "**Flowering Process**: A close-up of a colorful flower blooming on a mature plant, with intricate details of the petals and reproductive parts (stamens and pistils) clearly visible. Surrounding the flower are buzzing bees and butterflies, illustrating the interaction with pollinators that play a crucial role in the reproduction of the plant."
        },
        {
            "prompt": "**Fruiting and Seed Dispersal**: A dynamic scene showing a ripe fruit hanging from a branch, with sections cut open to reveal the seeds inside. Some seeds are being carried away by the wind or small animals, illustrating the dispersal mechanism. The background includes lush greenery and hints of other plants, emphasizing the biodiversity of the ecosystem."
        },
        {
            "prompt": "**Ecosystem Interaction**: A wide shot depicting a diverse landscape with various plant species, insects, and animals coexisting. The plants are shown in different growth stages, with some flowering and others bearing fruit, while various fauna interact with them. The scene should capture the interconnectedness of plants with their environment, showcasing how they contribute to the ecosystem."
        },
        {
            "prompt": "**Ecological Balance**: An overview illustration showing a thriving ecosystem composed of plants, animals, and natural elements like water and sunlight. This scene should depict a balance where plants provide oxygen and food, while animals contribute to pollination and seed dispersal. The backdrop includes a clear sky and a vibrant landscape, symbolizing the harmony of nature."
        },
    ],
    style="Phổ thông",
)
DUMMY_IMAGE_RESPONSE = CreateImageResponse(
    image_url="https://fastly.picsum.photos/id/364/536/354.jpg?hmac=3O0ojRh7NNfYP6PiPhbnupymAgRh1IUj7FK5zAOtrws"
)
DUMMY_AUDIO_RESPONSE = CreateAudioResponse(
    audio_url="https://commondatastorage.googleapis.com/codeskulptor-demos/DDR_assets/Kangaroo_MusiQue_-_The_Neverwritten_Role_Playing_Game.mp3",
    audio_duration=300,
)
