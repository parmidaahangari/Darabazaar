    function removeFromWishlist(productId) {
      fetch('{% url "remove_from_wishlist" %}', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': '{{ csrf_token }}'
        },
        body: `product_id=${productId}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          location.reload();
        } else {
          alert(data.message || 'خطا در حذف محصول');
        }
      });
    }
